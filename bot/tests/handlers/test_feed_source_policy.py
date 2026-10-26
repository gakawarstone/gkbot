from collections.abc import AsyncGenerator
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from urllib.parse import urlsplit

import pytest
from aiogram.types import CallbackQuery, Message

from modules.feed.handlers.callbacks import ItemEventHandler
from modules.feed.handlers.messages import ShowFeedItemsHandler
from modules.feed.handlers.policy import FeedSourcePolicy
from modules.feed.handlers.processors import FeedProcessor, FeedProcessorRegistry
from modules.feed.handlers.processors.matching import matches_source_url
from services.gkfeed import FeedItem, GkfeedApi, GkfeedCredentials, GkfeedItemsPicker


@pytest.fixture
def item() -> FeedItem:
    return FeedItem(1, 2, "https://example.invalid/article", "title", "text")


@pytest.mark.parametrize(
    ("link", "expected"),
    [
        ("https://example.invalid./article", True),
        ("https://example.invalid:443/article", True),
        ("http://example.invalid/article", False),
        ("https://example.invalid:80/article", False),
        ("https://user:password@example.invalid/article", False),
        ("https://example.invalid:not-a-port/article", False),
        ("https://example.invalid:65536/article", False),
        ("https://[example.invalid/article", False),
        ("https://example.invalid\n/article", False),
        ("https://example.invalid/a b", False),
        ("https:///example.invalid/article", False),
        ("//example.invalid/article", False),
    ],
)
def test_source_url_uses_parsed_authority(
    item: FeedItem, link: str, expected: bool
) -> None:
    assert (
        matches_source_url(replace(item, link=link), frozenset({"example.invalid"}))
        is expected
    )


@pytest.fixture
def registry() -> FeedProcessorRegistry:
    return FeedProcessorRegistry(
        (
            FeedProcessor(
                "restricted",
                lambda item: matches_source_url(
                    item, frozenset({"restricted.invalid", "alias.invalid"})
                ),
                AsyncMock(),
            ),
            FeedProcessor(
                "accepted",
                lambda item: matches_source_url(item, frozenset({"example.invalid"})),
                AsyncMock(),
            ),
        )
    )


@pytest.mark.parametrize(
    ("source_id", "link"),
    [
        ("stories", "https://stories.example/video.mp4"),
        ("kinogo", "https://kinogo.example/movie"),
        ("spoti", "https://open.spotify.com/album/1"),
        ("vk", "https://vk.com/wall-42_99"),
        ("youtube", "https://www.youtube.com/watch?v=video-code"),
        ("telegram", "https://t.me/channel/1"),
        ("reddit", "https://www.reddit.com/r/test/comments/post"),
        ("rezka", "https://hdrezka.me/film/1"),
        ("shiki", "https://shikimori.one/animes/1"),
        ("twitch", "https://www.twitch.tv/channel"),
        ("tiktok", "https://www.tiktok.com/@author/video/1"),
        ("pornhub", "https://www.pornhub.com/view_video.php?viewkey=key"),
        ("pornhub", "https://de.pornhub.org/view_video.php?viewkey=key"),
        ("pornhub", "https://pornhub.org/view_video.php?viewkey=key"),
        ("porno365", "http://porno365.broker/watch/1"),
        ("discours", "https://discours.io/articles/post"),
        ("instagram", "https://instagram.com/p/post"),
        ("instagram", "https://www.instagram.com/p/post"),
        ("hltv", "https://www.hltv.org/matches/1"),
        ("sasflix", "https://sasflix.ru/topics/uuid"),
        ("matreshka", "https://matreshka.tv/video/video-id"),
    ],
)
def test_real_sources_share_routing_and_policy_identity(
    item: FeedItem, source_id: str, link: str
) -> None:
    handler = ShowFeedItemsHandler(event=MagicMock(spec=Message))
    registry = handler._processor_registry
    item = replace(item, link=link)
    policy = FeedSourcePolicy(registry, frozenset({source_id}))
    assert not policy.allows(item)
    parsed = urlsplit(link)
    normalized_case = parsed._replace(
        scheme=parsed.scheme.upper(), netloc=parsed.netloc.upper()
    ).geturl()
    assert not policy.allows(replace(item, link=normalized_case))
    for deceptive_link in (
        f"{parsed.scheme}://{parsed.hostname}@unknown.invalid{parsed.path}",
        f"{parsed.scheme}://unknown.invalid/{parsed.hostname}{parsed.path}",
        f"{parsed.scheme}://unknown.invalid/?next={link}",
        f"{parsed.scheme}://unknown.invalid/#{link}",
    ):
        unknown = replace(item, link=deceptive_link)
        assert registry.resolve(unknown) is None
        assert policy.allows(unknown)
    if source_id not in {"stories", "kinogo"}:
        unknown = replace(
            item,
            link=f"{parsed.scheme}://{parsed.hostname}.evil.invalid{parsed.path}",
        )
        assert registry.resolve(unknown) is None
        assert policy.allows(unknown)


class PolicyMessageHandler(ShowFeedItemsHandler):
    @property
    async def _gkfeed_credentials(self) -> GkfeedCredentials:
        return GkfeedCredentials("policy-test", "password")


class PolicyCallbackHandler(ItemEventHandler):
    @property
    async def _gkfeed_credentials(self) -> GkfeedCredentials:
        return GkfeedCredentials("policy-test", "password")


@pytest.fixture(params=["message", "callback"])
def handler(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> PolicyMessageHandler | PolicyCallbackHandler:
    monkeypatch.setattr(GkfeedItemsPicker, "_items_pocket", {})
    event = MagicMock(spec=Message if request.param == "message" else CallbackQuery)
    message = event if request.param == "message" else MagicMock(spec=Message)
    message.answer = AsyncMock()
    message.delete = AsyncMock()
    if request.param == "callback":
        event.message = message
        event.data = "fd:keep:99"
        return PolicyCallbackHandler(event=event)
    return PolicyMessageHandler(event=event)


@pytest.mark.parametrize("selected_source", ["accepted", "unknown", "none"])
async def test_both_entry_points_apply_policy_before_selection(
    handler: PolicyMessageHandler | PolicyCallbackHandler,
    registry: FeedProcessorRegistry,
    item: FeedItem,
    selected_source: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    denied = replace(item, link="https://restricted.invalid/item")
    allowed = replace(
        item,
        id=3,
        link="https://example.invalid/3"
        if selected_source == "accepted"
        else "https://unknown.invalid/3",
    )

    async def get_items(self: GkfeedApi) -> AsyncGenerator[FeedItem]:
        yield denied
        if selected_source != "none":
            yield allowed

    monkeypatch.setattr(GkfeedApi, "get_user_items", get_items)
    monkeypatch.setattr(handler, "_rejected_source_ids", frozenset({"restricted"}))
    with (
        patch.object(
            type(handler), "_processor_registry", PropertyMock(return_value=registry)
        ),
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as generic,
    ):
        await handler.handle()

    message = (
        handler.event.message
        if isinstance(handler.event, CallbackQuery)
        else handler.event
    )
    assert isinstance(message, MagicMock)
    message.delete.assert_awaited_once()
    denied_entry, allowed_entry = registry.entries
    assert isinstance(denied_entry.process, AsyncMock)
    assert isinstance(allowed_entry.process, AsyncMock)
    denied_entry.process.assert_not_awaited()
    assert denied.id not in GkfeedItemsPicker._items_pocket["policy-test"]
    if selected_source == "none":
        allowed_entry.process.assert_not_awaited()
        generic.assert_not_awaited()
        message.answer.assert_awaited_once_with("На данный момент ничего нового")
        assert not GkfeedItemsPicker._items_pocket["policy-test"]
    else:
        message.answer.assert_not_awaited()
        assert GkfeedItemsPicker._items_pocket["policy-test"] == {allowed.id}
        if selected_source == "accepted":
            allowed_entry.process.assert_awaited_once_with(allowed)
            generic.assert_not_awaited()
        else:
            allowed_entry.process.assert_not_awaited()
            generic.assert_awaited_once_with(allowed)


async def test_picker_preserves_order_and_login_isolation_with_policy(
    registry: FeedProcessorRegistry,
    item: FeedItem,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    denied = replace(item, link="https://restricted.invalid/item")
    second_feed = replace(item, id=2, feed_id=3)
    same_feed = replace(item, id=3)

    async def get_items(self: GkfeedApi) -> AsyncGenerator[FeedItem]:
        for candidate in (same_feed, denied, second_feed):
            yield candidate

    monkeypatch.setattr(GkfeedItemsPicker, "_items_pocket", {})
    monkeypatch.setattr(GkfeedApi, "get_user_items", get_items)
    policy = FeedSourcePolicy(registry, frozenset({"restricted"}))
    first = GkfeedItemsPicker(GkfeedCredentials("first", "password"))
    second = GkfeedItemsPicker(GkfeedCredentials("second", "password"))
    assert await first.get_next_item(policy.allows) == same_feed
    assert await second.get_next_item(policy.allows) == same_feed
    assert await first.get_next_item(policy.allows) == second_feed
    assert await first.get_next_item(policy.allows) is None
    assert GkfeedItemsPicker._items_pocket["first"] == set()
    assert GkfeedItemsPicker._items_pocket["second"] == {same_feed.id}
    assert await first.get_next_item(policy.allows) == same_feed
