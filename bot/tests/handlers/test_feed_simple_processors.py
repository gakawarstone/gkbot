import asyncio
from dataclasses import dataclass, replace
from html import escape
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendPhoto
from aiogram.types import BufferedInputFile, CallbackQuery, Message, URLInputFile

from modules.feed.handlers.messages import ShowFeedItemsHandler
from modules.feed.handlers.processors import FeedProcessor, FeedProcessorRegistry
from modules.feed.handlers.processors._simple_rendering import (
    SendItem,
)
from modules.feed.handlers.processors._simple_rendering import (
    SendPhoto as PhotoSender,
)
from modules.feed.ui.keyboards import FeedMarkup
from services.gkfeed import FeedItem
from services.http import HttpRequestError, HttpService
from services.open_graph import OpenGraphService

IMAGE = "https://example.invalid/image.jpg"


@dataclass(frozen=True)
class SourceCase:
    source_id: str
    link: str
    html: str
    description: str
    link_caption: str = "Link"
    image: str = IMAGE


CASES = (
    SourceCase("kinogo", "https://kinogo.example/movie", f'<link href="{IMAGE}">', ""),
    SourceCase(
        "spoti",
        "https://open.spotify.com/album/1",
        f'<meta name="twitter:image" content="{IMAGE}">'
        '<meta name="twitter:title" content="Release - Single">'
        '<meta name="twitter:description" content="Artist · 2026">',
        "Release - Artist",
        "Spotify Release",
    ),
    SourceCase(
        "rezka",
        "https://hdrezka.me/film/1?preview=yes#poster",
        f'<meta property="og:image" content="{IMAGE}">',
        "Feed title",
    ),
    SourceCase(
        "shiki",
        "https://shikimori.one/animes/1",
        f'<meta property="og:image" content="{IMAGE}"><h1>Anime / Original</h1>',
        "Feed text",
        "Anime",
    ),
    SourceCase(
        "telegram",
        "https://t.me/channel/1",
        f'<meta property="og:image" content="{IMAGE}">'
        '<meta property="og:description" content="Channel post">',
        "Channel post",
    ),
    SourceCase(
        "twitch",
        "https://www.twitch.tv/channel/videos",
        "",
        "Feed text",
        "channel",
        "https://static-cdn.jtvnw.net/previews-ttv/live_user_channel-1920x1080.jpg",
    ),
    SourceCase(
        "hltv",
        "https://www.hltv.org/matches/1?x=1&y=2",
        '<meta property="og:image" content="http://example.invalid/image.jpg">'
        '<meta property="og:title" content="A &amp; B at Event">'
        '<script type="application/ld+json">{"startDate":"2026-10-23T12:30:00Z"}</script>',
        "",
    ),
)


@pytest.fixture(params=CASES, ids=lambda case: case.source_id)
def case(request: pytest.FixtureRequest) -> SourceCase:
    return request.param


@pytest.fixture
def item(case: SourceCase) -> FeedItem:
    return FeedItem(
        id=11, feed_id=22, link=case.link, title="Feed title", text="Feed text"
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


def assert_navigation(markup: object, item: FeedItem) -> None:
    expected = FeedMarkup.get_item_markup(item.id, item.feed_id)
    assert markup == expected
    assert [
        [button.callback_data for button in row] for row in expected.inline_keyboard
    ] == [
        [f"fd:show_all_feed:{item.feed_id}"],
        [f"fd:keep:{item.id}", f"fd:del:{item.id}"],
    ]


async def test_simple_source_renders_through_registry(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    case: SourceCase,
    event: MagicMock,
    bot: MagicMock,
) -> None:
    async def get(url: str, **kwargs: object) -> bytes:
        return b"image bytes" if url == IMAGE else case.html.encode()

    with (
        patch.object(HttpService, "get", side_effect=get) as http,
        patch.object(
            HttpService, "get_with_downloader", return_value=case.html.encode()
        ) as downloader,
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
    ):
        await handler._process_item(item)

    entry = handler._processor_registry.resolve(item)
    assert entry is not None and entry.source_id == case.source_id
    event.answer_photo.assert_awaited_once()
    photo = event.answer_photo.call_args.args[0]
    options = event.answer_photo.call_args.kwargs
    assert_navigation(options["reply_markup"], item)
    if case.source_id == "hltv":
        assert isinstance(photo, BufferedInputFile)
        assert photo.data == b"image bytes" and photo.filename == "hltv.png"
        assert (
            options["caption"]
            == f'<b>23.10.2026 12:30</b>\n\n<a href="{escape(item.link, quote=True)}">A &amp; B</a>'
        )
        downloader.assert_awaited_once()
        assert downloader.call_args.args == (item.link,)
        http.assert_awaited_once_with(IMAGE)
    else:
        assert isinstance(photo, URLInputFile) and photo.url == case.image
        assert (
            options["caption"]
            == f'<b>{case.description}</b>\n\n<a href="{item.link}">{case.link_caption}</a>'
        )
        assert options["has_spoiler"] is False
        downloader.assert_not_awaited()
        if case.source_id == "rezka":
            http.assert_awaited_once_with(
                "https://rezka.ag/film/1?preview=yes#poster",
                headers={"User-Agent": "TelegramBot (like TwitterBot)"},
            )
        elif case.source_id in {"kinogo", "spoti", "shiki"}:
            http.assert_awaited_once_with(item.link, headers=HttpService.headers)
        elif case.source_id == "twitch":
            http.assert_not_awaited()
        else:
            assert http.call_args.args == (item.link,)
    base.assert_not_awaited()
    bot.send_message.assert_not_awaited()


async def test_photo_rejection_keeps_navigation_and_plain_link(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    case: SourceCase,
    event: MagicMock,
    bot: MagicMock,
) -> None:
    event.answer_photo.side_effect = TelegramBadRequest(
        SendPhoto(chat_id=7, photo="photo"), "invalid photo"
    )
    with (
        patch.object(HttpService, "get", return_value=case.html.encode()),
        patch.object(
            HttpService, "get_with_downloader", return_value=case.html.encode()
        ),
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
    ):
        await handler._process_item(item)
    event.answer_photo.assert_awaited_once()
    bot.send_message.assert_awaited_once_with(
        7,
        f'<a href="{item.link}">{handler._get_item_link_caption(item)}</a>',
        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
    )
    base.assert_not_awaited()


@pytest.mark.parametrize(
    "failure",
    [HttpRequestError("private"), RuntimeError("bug"), asyncio.CancelledError()],
)
async def test_registered_source_keeps_execution_error_policy(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    case: SourceCase,
    event: MagicMock,
    bot: MagicMock,
    failure: BaseException,
    caplog: pytest.LogCaptureFixture,
) -> None:
    event.answer_photo.side_effect = failure
    with (
        patch.object(HttpService, "get", return_value=case.html.encode()),
        patch.object(
            HttpService, "get_with_downloader", return_value=case.html.encode()
        ),
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
    ):
        if isinstance(failure, HttpRequestError):
            await handler._process_item(item)
            bot.send_message.assert_awaited_once()
            assert caplog.records[0].args == (
                item.id,
                item.feed_id,
                len(item.text),
                case.source_id,
            )
            assert "private" not in caplog.text
        else:
            with pytest.raises(type(failure)) as raised:
                await handler._process_item(item)
            assert raised.value is failure
            bot.send_message.assert_not_awaited()
    base.assert_not_awaited()


@pytest.mark.parametrize("candidate", CASES, ids=lambda case: case.source_id)
def test_simple_source_matches_parsed_host(candidate: SourceCase) -> None:
    handler = ShowFeedItemsHandler(event=MagicMock(spec=Message))
    registry = handler._processor_registry
    item = FeedItem(id=1, feed_id=2, link=candidate.link, title="", text="")
    entry = registry.resolve(item)
    assert entry is not None and entry.source_id == candidate.source_id
    assert (
        entry.matches(replace(item, link=candidate.link.replace("https://", "http://")))
        is False
    )
    assert (
        entry.matches(
            replace(item, link=candidate.link.replace("https://", "HTTPS://"))
        )
        is True
    )
    assert entry.matches(replace(item, link="https://example.invalid")) is False
    host = candidate.link.split("/")[2]
    if candidate.source_id == "kinogo":
        # Its mirror hostname family stays compatible until hosts are enumerated.
        assert entry.matches(replace(item, link=f"https://{host}.other/extra"))
    else:
        assert not entry.matches(
            replace(item, link=f"https://{host}.evil.invalid/extra")
        )


def create_example_processor(
    send_photo: PhotoSender, send_item: SendItem
) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None:
            return await send_item(item)
        await send_photo(item, metadata.image_url, metadata.title or item.title)

    return FeedProcessor(
        "example", lambda item: item.link.startswith("https://example.invalid"), process
    )


class HandlerWithAnotherSource(ShowFeedItemsHandler):
    @property
    def _processor_registry(self) -> FeedProcessorRegistry:
        return FeedProcessorRegistry(
            (
                *super()._processor_registry.entries,
                create_example_processor(self._send_photo, self._send_item),
            )
        )


async def test_another_simple_source_needs_only_its_entry_and_composition(
    event: MagicMock,
    bot: MagicMock,
) -> None:
    handler = HandlerWithAnotherSource(event=event, bot=bot)
    item = FeedItem(
        id=11,
        feed_id=22,
        link="https://example.invalid/article",
        title="Example",
        text="",
    )
    with (
        patch.object(
            HttpService,
            "get",
            return_value=f'<meta property="og:image" content="{IMAGE}">'.encode(),
        ),
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
    ):
        await handler._process_item(item)
    event.answer_photo.assert_awaited_once()
    assert (
        event.answer_photo.call_args.kwargs["caption"]
        == f'<b>Example</b>\n\n<a href="{item.link}">Link</a>'
    )
    assert_navigation(event.answer_photo.call_args.kwargs["reply_markup"], item)
    base.assert_not_awaited()
    bot.send_message.assert_not_awaited()


@pytest.mark.parametrize(
    ("source", "html"),
    [
        ("kinogo", ""),
        ("kinogo", "<link>"),
        ("kinogo", '<link href="">'),
        ("spoti", ""),
        ("spoti", '<meta name="twitter:image">'),
        ("spoti", f'<meta name="twitter:image" content="{IMAGE}">'),
        (
            "spoti",
            f'<meta name="twitter:image" content="{IMAGE}"><meta name="twitter:title" content="title">',
        ),
        ("rezka", ""),
        ("telegram", f'<meta property="og:image" content="{IMAGE}">'),
        ("telegram", '<meta property="og:description" content="description">'),
        ("shiki", "<h1>Title</h1>"),
        ("shiki", f'<meta property="og:image" content="{IMAGE}">'),
        ("shiki", f'<meta property="og:image" content="{IMAGE}"><h1> / </h1>'),
        ("hltv", ""),
        ("twitch", ""),
    ],
)
async def test_missing_source_content_keeps_plain_link(
    handler: ShowFeedItemsHandler,
    event: MagicMock,
    bot: MagicMock,
    source: str,
    html: str,
) -> None:
    candidate = next(case for case in CASES if case.source_id == source)
    link = "https://www.twitch.tv/" if source == "twitch" else candidate.link
    item = FeedItem(id=11, feed_id=22, link=link, title="title", text="text")
    with (
        patch.object(HttpService, "get", return_value=html.encode()),
        patch.object(HttpService, "get_with_downloader", return_value=html.encode()),
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
    ):
        await handler._process_item(item)
    event.answer_photo.assert_not_awaited()
    bot.send_message.assert_awaited_once_with(
        7,
        f'<a href="{item.link}">{handler._get_item_link_caption(item)}</a>',
        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
    )
    base.assert_not_awaited()


@pytest.mark.parametrize(
    "source", [case.source_id for case in CASES if case.source_id != "twitch"]
)
async def test_source_http_error_falls_back_without_trying_generic_web(
    handler: ShowFeedItemsHandler,
    event: MagicMock,
    bot: MagicMock,
    source: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    candidate = next(case for case in CASES if case.source_id == source)
    item = FeedItem(id=11, feed_id=22, link=candidate.link, title="title", text="text")
    with (
        patch.object(HttpService, "get", side_effect=HttpRequestError("private URL")),
        patch.object(
            HttpService,
            "get_with_downloader",
            side_effect=HttpRequestError("private URL"),
        ),
        patch.object(handler, "_process_base_item", new_callable=AsyncMock) as base,
    ):
        await handler._process_item(item)
    event.answer_photo.assert_not_awaited()
    bot.send_message.assert_awaited_once()
    base.assert_not_awaited()
    assert caplog.records[0].args == (item.id, item.feed_id, len(item.text), source)
    assert "private URL" not in caplog.text


@pytest.mark.parametrize("length", [249, 250, 251])
async def test_telegram_description_length_boundary(
    handler: ShowFeedItemsHandler,
    event: MagicMock,
    length: int,
) -> None:
    description = "x" * length
    item = FeedItem(
        id=11, feed_id=22, link="https://t.me/channel/1", title="title", text=""
    )
    html = f'<meta property="og:image" content="{IMAGE}"><meta property="og:description" content="{description}">'
    with patch.object(HttpService, "get", return_value=html.encode()):
        await handler._process_item(item)
    expected = description if length <= 250 else "x" * 247 + "..."
    assert (
        event.answer_photo.call_args.kwargs["caption"]
        == f'<b>{expected}</b>\n\n<a href="{item.link}">Link</a>'
    )


async def test_spotify_playlist_caption(
    handler: ShowFeedItemsHandler, event: MagicMock
) -> None:
    item = FeedItem(
        id=11,
        feed_id=22,
        link="https://open.spotify.com/playlist/1",
        title="title",
        text="",
    )
    html = f'<meta name="twitter:image" content="{IMAGE}"><meta name="twitter:title" content="My playlist"><meta name="twitter:description" content="Playlist · User">'
    with patch.object(HttpService, "get", return_value=html.encode()):
        await handler._process_item(item)
    assert (
        event.answer_photo.call_args.kwargs["caption"]
        == f'<b></b>\n\n<a href="{item.link}">My playlist</a>'
    )


@pytest.mark.parametrize(
    "image_markup",
    [
        '<div class="b-db_entry-poster"><picture><img src="//example.invalid/image.jpg"></picture></div>',
        '<meta itemprop="image" content=" //example.invalid/image.jpg ">',
        '<picture><source srcset="small.jpg 1x, //example.invalid/image.jpg 2x"></picture>',
        '<meta property="og:image" content="//example.invalid/image.jpg">',
    ],
)
async def test_shiki_image_variants_and_title(
    handler: ShowFeedItemsHandler,
    event: MagicMock,
    image_markup: str,
) -> None:
    item = FeedItem(
        id=11,
        feed_id=22,
        link="https://shikimori.one/animes/1",
        title="title",
        text="Description",
    )
    html = image_markup + "<h1> Anime <span>name</span> / Original </h1>"
    with patch.object(HttpService, "get", return_value=html.encode()):
        await handler._process_item(item)
    photo = event.answer_photo.call_args.args[0]
    assert isinstance(photo, URLInputFile) and photo.url == IMAGE
    assert (
        event.answer_photo.call_args.kwargs["caption"]
        == f'<b>Description</b>\n\n<a href="{item.link}">Anime name</a>'
    )


@pytest.mark.parametrize(
    "event_json", [None, "{", '{"startDate":"bad date"}', '{"startDate":123}', "{}"]
)
async def test_hltv_without_valid_time_keeps_matchup(
    handler: ShowFeedItemsHandler,
    event: MagicMock,
    event_json: str | None,
) -> None:
    item = FeedItem(
        id=11,
        feed_id=22,
        link="https://www.hltv.org/matches/1",
        title="Feed & title at Event",
        text="",
    )
    html = f'<meta property="og:image" content="{IMAGE}">'
    if event_json is not None:
        html += f'<script type="application/ld+json">{event_json}</script>'
    with (
        patch.object(HttpService, "get_with_downloader", return_value=html.encode()),
        patch.object(HttpService, "get", return_value=b"image bytes"),
    ):
        await handler._process_item(item)
    assert (
        event.answer_photo.call_args.kwargs["caption"]
        == f'<a href="{item.link}">Feed &amp; title</a>'
    )


async def test_twitch_uses_feed_title_for_empty_text(
    handler: ShowFeedItemsHandler,
    event: MagicMock,
) -> None:
    item = FeedItem(
        id=11,
        feed_id=22,
        link="https://www.twitch.tv/channel",
        title="Feed title",
        text="",
    )
    await handler._process_item(item)
    assert (
        event.answer_photo.call_args.kwargs["caption"]
        == f'<b>Feed title</b>\n\n<a href="{item.link}">channel</a>'
    )
