import asyncio
import json
import os
from collections.abc import AsyncIterator
from pathlib import Path
from time import monotonic
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import BufferedInputFile, CallbackQuery, Message, URLInputFile

from modules.feed.handlers.callbacks import ItemEventHandler
from modules.feed.handlers.messages import ShowFeedItemsHandler
from modules.feed.ui.keyboards import FeedMarkup
from services.gkfeed import FeedItem, GkfeedCredentials
from services.gkfeed.api import GkfeedApi
from services.gkfeed.picker import GkfeedItemsPicker
from services.http import HttpService
from services.matreshka import MatreshkaService
from services.open_graph import OpenGraphService
from services.telegraph import TelegraphAPI
from workers.feed_parser import feed_parser

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(scope="module", autouse=True)
async def parser() -> AsyncIterator[None]:
    await feed_parser.start()
    try:
        yield
    finally:
        await feed_parser.close()


def _parse_until_released(started: str, release: str) -> int:
    """Keep doing real HTML parsing until the callback can delete its message."""
    Path(started).write_text(str(os.getpid()))
    deadline = monotonic() + 10
    html = b"<div><p>text</p><a href='/'>link</a></div>" * 1000
    while not Path(release).exists():
        OpenGraphService.parse(html)
        if monotonic() >= deadline:
            raise TimeoutError("Callback did not release the parser")
    return os.getpid()


class PreviewHandler(ShowFeedItemsHandler):
    @property
    async def _gkfeed_credentials(self) -> GkfeedCredentials:
        return GkfeedCredentials("test", "test")


async def show_item(item: FeedItem, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    event = MagicMock(spec=Message)
    event.from_user = MagicMock(id=42)
    event.bot = MagicMock()
    event.delete = AsyncMock()
    event.answer = AsyncMock()
    event.answer_photo = AsyncMock()
    event.bot.send_message = AsyncMock()
    monkeypatch.setattr(
        GkfeedItemsPicker, "get_next_item", AsyncMock(return_value=item)
    )
    await PreviewHandler(event=event, bot=event.bot).handle()
    event.delete.assert_awaited_once()
    return event


async def test_delete_can_run_while_another_preview_keeps_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started = tmp_path / "started"
    release = tmp_path / "release"
    parsing = asyncio.create_task(
        feed_parser.run(_parse_until_released, str(started), str(release))
    )
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "feed:del:1"
    callback.message = MagicMock(spec=Message)
    deleted = asyncio.Event()

    async def delete_message() -> None:
        assert not parsing.done()
        deleted.set()

    callback.message.delete = AsyncMock(side_effect=delete_message)
    callback.message.answer = AsyncMock()

    class Handler(ItemEventHandler):
        @property
        async def _gkfeed_credentials(self) -> GkfeedCredentials:
            return GkfeedCredentials("test", "test")

    delete_item = AsyncMock()
    monkeypatch.setattr(GkfeedApi, "delete_item_by_id", delete_item)
    monkeypatch.setattr(
        GkfeedItemsPicker, "get_next_item", AsyncMock(return_value=None)
    )
    try:
        async with asyncio.timeout(5):
            while not started.exists():
                await asyncio.sleep(0.01)
            assert int(started.read_text()) != os.getpid()
            await Handler(event=callback).handle()
            assert deleted.is_set()
            delete_item.assert_awaited_once_with(1)
            callback.message.answer.assert_awaited_once_with(
                "На данный момент ничего нового"
            )
    finally:
        release.touch()
        await parsing


@pytest.mark.parametrize(
    ("link", "html", "image", "caption"),
    [
        (
            "https://example.invalid/post",
            '<meta property="og:image" content="https://image.invalid/og"><meta property="og:title" content="OG title">',
            "https://image.invalid/og",
            'OG title</b>\n\n<a href="https://example.invalid/post">Link',
        ),
        (
            "https://kinogo.invalid/post",
            '<link href="https://image.invalid/kinogo">',
            "https://image.invalid/kinogo",
            '</b>\n\n<a href="https://kinogo.invalid/post">Link',
        ),
        (
            "https://open.spotify.com/album/offline",
            '<meta name="twitter:image" content="https://image.invalid/spoti"><meta name="twitter:title" content="Album - Artist"><meta name="twitter:description" content="Artist · Album">',
            "https://image.invalid/spoti",
            'Album - Artist</b>\n\n<a href="https://open.spotify.com/album/offline">Spotify Release',
        ),
        (
            "https://shikimori.one/animes/offline",
            '<h1>Anime / Other title</h1><div class="b-db_entry-poster"><picture><img src="//image.invalid/shiki"></picture></div>',
            "https://image.invalid/shiki",
            'description</b>\n\n<a href="https://shikimori.one/animes/offline">Anime',
        ),
    ],
)
async def test_source_previews_keep_media_and_captions(
    monkeypatch: pytest.MonkeyPatch, link: str, html: str, image: str, caption: str
) -> None:
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=html.encode()))
    item = FeedItem(1, 2, link, "title", "description")
    event = await show_item(item, monkeypatch)
    event.answer_photo.assert_awaited_once()
    photo = event.answer_photo.call_args.args[0]
    assert isinstance(photo, URLInputFile)
    assert photo.url == image
    assert event.answer_photo.call_args.kwargs["caption"] == f"<b>{caption}</a>"
    assert event.answer_photo.call_args.kwargs[
        "reply_markup"
    ] == FeedMarkup.get_item_markup(1, 2)
    event.bot.send_message.assert_not_awaited()


async def test_vk_text_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        HttpService,
        "get",
        AsyncMock(
            return_value=b'<title>Post | Channel</title><meta property="og:description" content="Body">'
        ),
    )
    event = await show_item(
        FeedItem(1, 2, "https://vk.com/wall1_2", "title", "description"), monkeypatch
    )
    event.answer.assert_awaited_once_with(
        "<b>Body</b>\n\n<a href='https://vk.com/wall1_2'>Channel</a>",
        reply_markup=FeedMarkup.get_item_markup(1, 2),
        disable_web_page_preview=True,
    )


async def test_instagram_hltv_and_matreshka_return_ready_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event = await show_item(
        FeedItem(
            1,
            2,
            "https://instagram.com/offline",
            "user:caption",
            '<img src="data:image/png;base64,YWJj">',
        ),
        monkeypatch,
    )
    event.answer_photo.assert_awaited_once()
    photo = event.answer_photo.call_args.args[0]
    assert isinstance(photo, BufferedInputFile)
    assert photo.data == b"abc"
    assert event.answer_photo.call_args.kwargs["caption"] == "caption"
    assert event.answer_photo.call_args.kwargs[
        "reply_markup"
    ] == FeedMarkup.get_item_markup(1, 2)

    page = (
        b'<meta property="og:image" content="https://image.invalid/hltv">'
        b'<meta property="og:title" content="Team A vs Team B at event">'
        b'<script type="application/ld+json">{"startDate":"2026-10-28T12:00:00"}</script>'
    )
    monkeypatch.setattr(
        HttpService, "get_with_downloader", AsyncMock(return_value=page)
    )
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=b"image"))
    event = await show_item(
        FeedItem(1, 2, "https://www.hltv.org/matches/offline", "title", ""), monkeypatch
    )
    event.answer_photo.assert_awaited_once()
    photo = event.answer_photo.call_args.args[0]
    assert isinstance(photo, BufferedInputFile)
    assert photo.data == b"image"
    assert (
        event.answer_photo.call_args.kwargs["caption"]
        == '<b>28.10.2026 12:00</b>\n\n<a href="https://www.hltv.org/matches/offline">Team A vs Team B</a>'
    )
    assert event.answer_photo.call_args.kwargs[
        "reply_markup"
    ] == FeedMarkup.get_item_markup(1, 2)

    page = (
        b'<meta property="og:title" content="Video">'
        b'<meta property="video:duration" content="13">'
        b'<script>"https:\\u002F\\u002Fvideo.invalid/master.m3u8?x=1"</script>'
    )
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=page))
    video = await MatreshkaService.get_video("https://matreshka.tv/video/offline")
    assert (video.id, video.title, video.duration, video.hls_url) == (
        "offline",
        "Video",
        13,
        "https://video.invalid/master.m3u8?x=1",
    )

    invalid = FeedItem(3, 2, "https://instagram.com/invalid", "user:caption", "")
    event = await show_item(invalid, monkeypatch)
    event.bot.send_message.assert_awaited_once_with(
        42,
        '<a href="https://instagram.com/invalid">instagram</a>',
        reply_markup=FeedMarkup.get_item_markup(3, 2),
    )
    event.answer_photo.assert_not_awaited()
    assert (
        await MatreshkaService.get_video("https://matreshka.tv/video/offline") == video
    )


async def test_reddit_fallback_converts_body_before_sending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = b'<title>Title - Subreddit</title><div class="post"><div class="post_body"><p>Text <b>bold</b></p></div></div>'
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=html))
    create_page = AsyncMock(return_value="https://telegra.ph/offline")
    monkeypatch.setattr(TelegraphAPI, "create_telegraph_page", create_page)
    event = await show_item(
        FeedItem(1, 2, "https://www.reddit.com/r/offline", "title", ""), monkeypatch
    )
    assert create_page.call_args.kwargs["title"] == "Title"
    assert json.loads(create_page.call_args.kwargs["content"]) == [
        {"tag": "p", "children": ["Text ", {"tag": "b", "children": ["bold"]}]}
    ]
    event.answer.assert_awaited_once()
    assert (
        event.answer.call_args.args[0]
        == '<b>Title </b>\n\n<a href="https://www.reddit.com/r/offline">Subreddit</a>'
    )
    markup = event.answer.call_args.kwargs["reply_markup"]
    assert markup.inline_keyboard[0][0].url == "https://telegra.ph/offline"

    monkeypatch.setattr(
        HttpService,
        "get",
        AsyncMock(
            return_value=b'<div class="post"><img alt="Post image" src="image"></div>'
        ),
    )
    event = await show_item(
        FeedItem(1, 2, "https://www.reddit.com/r/offline", "title", ""), monkeypatch
    )
    event.answer_photo.assert_awaited_once()
    assert (
        event.answer_photo.call_args.args[0].url == "https://libreddit.qwik.space/image"
    )
