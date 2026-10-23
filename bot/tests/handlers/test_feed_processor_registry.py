import asyncio
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendPhoto
from aiogram.types import CallbackQuery, Message, URLInputFile

from modules.feed.handlers.messages import ShowFeedItemsHandler
from modules.feed.handlers.processors import FeedProcessor, FeedProcessorRegistry
from modules.feed.handlers.processors.discours import create_discours_processor
from modules.feed.ui.keyboards import FeedMarkup
from services.gkfeed import FeedItem
from services.http import HttpRequestError


@pytest.fixture
def item() -> FeedItem:
    return FeedItem(
        id=11,
        feed_id=22,
        link="https://discours.io/articles/post",
        title="Feed title",
        text="Feed text",
    )


@pytest.fixture(params=[Message, CallbackQuery], ids=["message", "callback"])
def event(request: pytest.FixtureRequest) -> MagicMock:
    event = MagicMock(spec=request.param)
    event.from_user = MagicMock(id=7)
    event.answer_photo = AsyncMock()
    if request.param is CallbackQuery:
        event.message = MagicMock(spec=Message)
        event.message.answer_photo = event.answer_photo
    return event


@pytest.fixture
def bot() -> MagicMock:
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def handler(event: MagicMock, bot: MagicMock) -> ShowFeedItemsHandler:
    return ShowFeedItemsHandler(event=event, bot=bot)


def test_registry_resolves_first_match_without_processing(item: FeedItem) -> None:
    skipped = FeedProcessor("skipped", lambda _: False, AsyncMock())
    first = FeedProcessor("first", lambda _: True, AsyncMock())
    last_match = MagicMock(return_value=True)
    last = FeedProcessor("last", last_match, AsyncMock())
    entries = [skipped, first, last]
    registry = FeedProcessorRegistry(iter(entries))
    entries.clear()

    assert registry.entries == (skipped, first, last)
    assert registry.resolve(item) is first
    assert registry.resolve(replace(item, id=33)) is first
    for entry in registry.entries:
        assert isinstance(entry.process, AsyncMock)
        entry.process.assert_not_called()
    last_match.assert_not_called()


def test_registry_unknown_source_and_duplicate_identity(item: FeedItem) -> None:
    entry = FeedProcessor("discours", lambda _: False, AsyncMock())
    assert FeedProcessorRegistry(()).resolve(item) is None
    assert FeedProcessorRegistry((entry,)).resolve(item) is None
    with pytest.raises(ValueError, match="identities must be unique"):
        FeedProcessorRegistry((entry, replace(entry, matches=lambda _: True)))


@pytest.mark.parametrize(
    ("link", "matches"),
    [
        ("https://discours.io/articles/post", True),
        ("https://discours.io/", True),
        ("https://discours.io.example/articles/post", True),
        ("http://discours.io/articles/post", False),
        ("https://www.discours.io/articles/post", False),
        ("https://example.invalid", False),
    ],
)
def test_discours_preserves_existing_prefix_matching(
    item: FeedItem, link: str, matches: bool
) -> None:
    entry = create_discours_processor(AsyncMock())
    assert entry.source_id == "discours"
    assert entry.matches(replace(item, link=link)) is matches


async def test_discours_renders_photo_through_registry(
    handler: ShowFeedItemsHandler, item: FeedItem, event: MagicMock, bot: MagicMock
) -> None:
    with (
        patch(
            "modules.feed.handlers.processors.discours.HttpService.get_json",
            return_value={"data": {"title": "API title", "thumborId": "image-id"}},
        ) as get_json,
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
    ):
        await handler._process_item(item)

    get_json.assert_awaited_once_with(
        "https://api.discours.io/api/v2/content-items/post"
    )
    photo = event.answer_photo.call_args.args[0]
    assert isinstance(photo, URLInputFile)
    assert photo.url == "https://assets.discours.io/unsafe/900x/image-id"
    event.answer_photo.assert_awaited_once_with(
        photo,
        caption=f'<b>API title</b>\n\n<a href="{item.link}">Link</a>',
        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        has_spoiler=False,
    )
    assert not hasattr(handler, "_process_discours_item")
    assert "https://discours.io" not in handler._processors
    bot.send_message.assert_not_awaited()
    base.assert_not_awaited()


@pytest.mark.parametrize("failure", ["http", "photo"])
async def test_discours_failure_keeps_plain_link_fallback(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    failure: str,
    caplog: pytest.LogCaptureFixture,
    event: MagicMock,
    bot: MagicMock,
) -> None:
    if failure == "photo":
        event.answer_photo.side_effect = TelegramBadRequest(
            SendPhoto(chat_id=7, photo="image"), "invalid media"
        )
    with (
        patch(
            "modules.feed.handlers.processors.discours.HttpService.get_json",
            return_value={"data": {"title": "API title", "thumborId": "image-id"}},
            side_effect=HttpRequestError("private-payload")
            if failure == "http"
            else None,
        ),
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
    ):
        await handler._process_item(item)

    bot.send_message.assert_awaited_once_with(
        7,
        f'<a href="{item.link}">discours</a>',
        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
    )
    base.assert_not_awaited()
    if failure == "http":
        event.answer_photo.assert_not_awaited()
        assert caplog.records[0].args == (
            item.id,
            item.feed_id,
            len(item.text),
            "discours",
        )
        assert "private-payload" not in caplog.text
    else:
        assert not caplog.records


@pytest.mark.parametrize("error", [KeyError("data"), asyncio.CancelledError()])
async def test_registry_processor_unexpected_error_propagates(
    handler: ShowFeedItemsHandler, item: FeedItem, error: BaseException, bot: MagicMock
) -> None:
    with (
        patch(
            "modules.feed.handlers.processors.discours.HttpService.get_json",
            side_effect=error,
        ),
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
        pytest.raises(type(error)) as raised,
    ):
        await handler._process_item(item)
    assert raised.value is error
    bot.send_message.assert_not_awaited()
    base.assert_not_awaited()


async def test_registry_fallback_failure_propagates_once(
    handler: ShowFeedItemsHandler, item: FeedItem, bot: MagicMock
) -> None:
    error = HttpRequestError("fallback failed")
    bot.send_message.side_effect = error
    with (
        patch(
            "modules.feed.handlers.processors.discours.HttpService.get_json",
            side_effect=HttpRequestError(),
        ),
        pytest.raises(HttpRequestError) as raised,
    ):
        await handler._process_item(item)
    assert raised.value is error
    bot.send_message.assert_awaited_once()


async def test_matching_errors_are_outside_execution_boundary(
    handler: ShowFeedItemsHandler, item: FeedItem, bot: MagicMock
) -> None:
    error = HttpRequestError("bad matcher")
    entry = FeedProcessor("broken", MagicMock(side_effect=error), AsyncMock())
    with (
        patch.object(
            type(handler),
            "_processor_registry",
            new_callable=PropertyMock,
            return_value=FeedProcessorRegistry((entry,)),
        ),
        pytest.raises(HttpRequestError) as raised,
    ):
        await handler._process_item(item)
    assert raised.value is error
    bot.send_message.assert_not_awaited()


async def test_registry_takes_precedence_over_legacy_dispatch(
    handler: ShowFeedItemsHandler, item: FeedItem, bot: MagicMock
) -> None:
    item = replace(item, link="https://www.twitch.tv/channel")
    process = AsyncMock()
    entry = FeedProcessor("registered", lambda _: True, process)
    with (
        patch.object(
            type(handler),
            "_processor_registry",
            new_callable=PropertyMock,
            return_value=FeedProcessorRegistry((entry,)),
        ),
        patch.object(handler, "_process_twitch_item", new_callable=AsyncMock) as legacy,
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
    ):
        await handler._process_item(item)
    process.assert_awaited_once_with(item)
    legacy.assert_not_awaited()
    base.assert_not_awaited()
    bot.send_message.assert_not_awaited()


@pytest.mark.parametrize(
    ("link", "method"),
    [
        ("https://stories.example/1", "_process_stories_item"),
        ("https://kinogo.example/1", "_process_kinogo_item"),
        ("https://open.spotify.com/1", "_process_spoti_item"),
        ("https://vk.com/1", "_process_vk_item"),
        ("https://www.youtube.com/1", "_process_youtube_item"),
        ("https://t.me/1", "_process_telegram_item"),
        ("https://www.reddit.com/1", "_process_reddit_item"),
        ("https://hdrezka.me/1", "_process_rezka_item"),
        ("https://shikimori.one/1", "_process_shiki_item"),
        ("https://www.twitch.tv/1", "_process_twitch_item"),
        ("https://www.tiktok.com/1", "_process_tiktok_item"),
        ("https://www.pornhub.com/1", "_process_pornhub_item"),
        ("https://de.pornhub.org/1", "_process_pornhub_item"),
        ("https://pornhub.org/1", "_process_pornhub_item"),
        ("http://porno365.broker/1", "_process_porno365_item"),
        ("https://instagram.com/1", "_process_instagram_item"),
        ("https://www.instagram.com/1", "_process_instagram_item"),
        ("https://www.hltv.org/1", "_process_hltv_item"),
        ("https://sasflix.ru/1", "_process_sasflix_item"),
        ("https://matreshka.tv/video/1", "_process_matreshka_item"),
        ("https://example.invalid", "_process_base_item"),
    ],
)
async def test_remaining_sources_keep_legacy_dispatch(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    link: str,
    method: str,
    bot: MagicMock,
) -> None:
    item = replace(item, link=link)
    with (
        patch.object(handler, method, new_callable=AsyncMock) as process,
        patch(
            "modules.feed.handlers.processors.discours.HttpService.get_json"
        ) as get_json,
    ):
        await handler._process_item(item)
    process.assert_awaited_once_with(item)
    get_json.assert_not_called()
    bot.send_message.assert_not_awaited()
