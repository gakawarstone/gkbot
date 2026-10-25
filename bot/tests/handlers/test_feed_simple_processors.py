import asyncio
from dataclasses import dataclass
from html import escape
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendPhoto
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    Message,
    URLInputFile,
)

from modules.feed.handlers.messages import ShowFeedItemsHandler
from services.gkfeed import FeedItem
from services.http import HttpRequestError, HttpService

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


def assert_navigation(markup: InlineKeyboardMarkup, item: FeedItem) -> None:
    assert {
        button.callback_data for row in markup.inline_keyboard for button in row
    } == {
        f"fd:show_all_feed:{item.feed_id}",
        f"fd:keep:{item.id}",
        f"fd:del:{item.id}",
    }


def assert_plain_link(bot: MagicMock, item: FeedItem) -> None:
    bot.send_message.assert_awaited_once()
    message = bot.send_message.call_args
    assert message.args[0] == 7
    assert f'href="{item.link}"' in message.args[1]
    assert_navigation(message.kwargs["reply_markup"], item)


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
        ),
    ):
        await handler._process_item(item)

    event.answer_photo.assert_awaited_once()
    photo = event.answer_photo.call_args.args[0]
    options = event.answer_photo.call_args.kwargs
    assert_navigation(options["reply_markup"], item)
    if case.source_id == "hltv":
        assert isinstance(photo, BufferedInputFile)
        assert photo.data == b"image bytes"
        assert (
            options["caption"]
            == f'<b>23.10.2026 12:30</b>\n\n<a href="{escape(item.link, quote=True)}">A &amp; B</a>'
        )
    else:
        assert isinstance(photo, URLInputFile) and photo.url == case.image
        assert (
            options["caption"]
            == f'<b>{case.description}</b>\n\n<a href="{item.link}">{case.link_caption}</a>'
        )
        if case.source_id == "rezka":
            http.assert_awaited_once_with(
                "https://rezka.ag/film/1?preview=yes#poster",
                headers={"User-Agent": "TelegramBot (like TwitterBot)"},
            )
    bot.send_message.assert_not_awaited()


@pytest.mark.parametrize(
    "case", [CASES[0], CASES[-1]], ids=["url-photo", "buffered-photo"]
)
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
    ):
        await handler._process_item(item)
    event.answer_photo.assert_awaited_once()
    assert_plain_link(bot, item)


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("bug"), asyncio.CancelledError()],
)
@pytest.mark.parametrize(
    "case", [CASES[5], CASES[-1]], ids=["url-photo", "buffered-photo"]
)
async def test_registered_source_keeps_execution_error_policy(
    handler: ShowFeedItemsHandler,
    item: FeedItem,
    case: SourceCase,
    event: MagicMock,
    bot: MagicMock,
    failure: BaseException,
) -> None:
    event.answer_photo.side_effect = failure
    with (
        patch.object(HttpService, "get", return_value=case.html.encode()),
        patch.object(
            HttpService, "get_with_downloader", return_value=case.html.encode()
        ),
    ):
        with pytest.raises(type(failure)) as raised:
            await handler._process_item(item)
        assert raised.value is failure
        bot.send_message.assert_not_awaited()


@pytest.mark.parametrize(
    ("source", "html"),
    [
        ("kinogo", "<link>"),
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
    ):
        await handler._process_item(item)
    event.answer_photo.assert_not_awaited()
    assert_plain_link(bot, item)


@pytest.mark.parametrize("source", ["kinogo", "hltv"])
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
    ):
        await handler._process_item(item)
    event.answer_photo.assert_not_awaited()
    assert_plain_link(bot, item)
    assert "private URL" not in caplog.text


@pytest.mark.parametrize("length", [250, 251])
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
    "event_json", [None, "{", '{"startDate":"bad date"}', '{"startDate":123}']
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
