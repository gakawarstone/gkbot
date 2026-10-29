import asyncio
import json
import os
from collections.abc import AsyncIterator
from pathlib import Path
from time import monotonic
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from modules.feed.handlers.callbacks import ItemEventHandler
from modules.feed.handlers.messages import ShowFeedItemsHandler
from modules.feed.handlers.views.reddit import RedditFeedItemView
from modules.feed.ui.keyboards import FeedMarkup
from services.feed_parser import feed_parser
from services.gkfeed import FeedItem, GkfeedCredentials
from services.gkfeed.api import GkfeedApi
from services.http import HttpService
from services.matreshka import MatreshkaService
from services.open_graph import OpenGraphService
from services.telegraph import TelegraphAPI

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


async def test_delete_can_run_while_another_preview_keeps_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started = tmp_path / "started"
    release = tmp_path / "release"
    parsing = asyncio.create_task(
        feed_parser.run(_parse_until_released, str(started), str(release))
    )
    callback = MagicMock(spec=CallbackQuery)
    callback.message = MagicMock(spec=Message)
    deleted = asyncio.Event()

    async def delete_message() -> None:
        assert not parsing.done()
        deleted.set()

    callback.message.delete = AsyncMock(side_effect=delete_message)

    class Handler(ItemEventHandler):
        @property
        async def _gkfeed_credentials(self) -> GkfeedCredentials:
            return GkfeedCredentials("test", "test")

    delete_item = AsyncMock()
    monkeypatch.setattr(GkfeedApi, "delete_item_by_id", delete_item)
    try:
        async with asyncio.timeout(5):
            while not started.exists():
                await asyncio.sleep(0.01)
            assert int(started.read_text()) != os.getpid()
            await Handler(event=callback)._handle_event("del", 1)
            assert deleted.is_set()
            await asyncio.sleep(0)
            delete_item.assert_awaited_once_with(1)
    finally:
        release.touch()
        await parsing


async def test_source_previews_keep_media_and_captions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler = ShowFeedItemsHandler(event=MagicMock(spec=Message))
    send_photo = AsyncMock()
    send_item = AsyncMock()
    answer = AsyncMock()
    monkeypatch.setattr(handler, "_send_photo", send_photo)
    monkeypatch.setattr(handler, "_send_item", send_item)
    monkeypatch.setattr(handler, "answer", answer)

    # Exercise source dispatch through the real multiple-inheritance handler.
    cases = [
        (
            "https://example.invalid/post",
            (
                '<meta property="og:image" content="https://image.invalid/og">'
                '<meta property="og:title" content="OG title">'
            ),
            ("https://image.invalid/og", "OG title"),
        ),
        (
            "https://kinogo.invalid/post",
            '<link href="https://image.invalid/kinogo">',
            ("https://image.invalid/kinogo", ""),
        ),
        (
            "https://open.spotify.com/album/offline",
            (
                '<meta name="twitter:image" content="https://image.invalid/spoti">'
                '<meta name="twitter:title" content="Album - Artist">'
                '<meta name="twitter:description" content="Artist · Album">'
            ),
            ("https://image.invalid/spoti", "Album - Artist", "Spotify Release"),
        ),
        (
            "https://shikimori.one/animes/offline",
            (
                '<h1>Anime / Other title</h1><div class="b-db_entry-poster">'
                '<picture><img src="//image.invalid/shiki"></picture></div>'
            ),
            ("https://image.invalid/shiki", "description", "Anime"),
        ),
    ]
    for link, html, expected in cases:
        item = FeedItem(1, 2, link, "title", "description")
        monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=html.encode()))
        send_photo.reset_mock()
        await handler._process_item(item)
        send_photo.assert_awaited_once_with(item, *expected)
    send_item.assert_not_awaited()

    item = FeedItem(1, 2, "https://vk.com/wall1_2", "title", "description")
    monkeypatch.setattr(
        HttpService,
        "get",
        AsyncMock(
            return_value=b"<title>Post | Channel</title>"
            b'<meta property="og:description" content="Body">'
        ),
    )
    await handler._process_item(item)
    answer.assert_awaited_once_with(
        "<b>Body</b>\n\n<a href='https://vk.com/wall1_2'>Channel</a>",
        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        disable_web_page_preview=True,
    )


async def test_instagram_hltv_and_matreshka_return_ready_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler = ShowFeedItemsHandler(event=MagicMock(spec=Message))
    answer_photo = AsyncMock()
    monkeypatch.setattr(handler, "answer_photo", answer_photo)
    item = FeedItem(
        1,
        2,
        "https://instagram.com/offline",
        "user:caption",
        '<img src="data:image/png;base64,YWJj">',
    )
    await handler._process_item(item)
    photo = answer_photo.call_args.args[0]
    assert isinstance(photo, BufferedInputFile)
    assert photo.data == b"abc"
    assert answer_photo.call_args.kwargs["caption"] == "caption"
    answer_photo.reset_mock()

    page = (
        b'<meta property="og:image" content="https://image.invalid/hltv">'
        b'<meta property="og:title" content="Team A vs Team B at event">'
        b'<script type="application/ld+json">{"startDate":"2026-10-28T12:00:00"}</script>'
    )
    monkeypatch.setattr(
        HttpService, "get_with_downloader", AsyncMock(return_value=page)
    )
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=b"image"))
    item = FeedItem(1, 2, "https://www.hltv.org/matches/offline", "title", "")
    await handler._process_item(item)
    photo = answer_photo.call_args.args[0]
    assert photo.data == b"image"
    assert answer_photo.call_args.kwargs["caption"] == (
        '<b>28.10.2026 12:00</b>\n\n<a href="https://www.hltv.org/matches/offline">Team A vs Team B</a>'
    )

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

    fallback = AsyncMock()
    monkeypatch.setattr(handler, "_send_item", fallback)
    invalid = FeedItem(3, 2, "https://instagram.com/invalid", "user:caption", "")
    await handler._process_item(invalid)
    fallback.assert_awaited_once_with(invalid)
    # A failed job must not prevent subsequent previews from being parsed.
    assert (
        await MatreshkaService.get_video("https://matreshka.tv/video/offline")
    ) == video


async def test_reddit_fallback_converts_body_before_returning_to_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler = ShowFeedItemsHandler(event=MagicMock(spec=Message))
    html = b'<title>Title - Subreddit</title><div class="post"><div class="post_body"><p>Text <b>bold</b></p></div></div>'
    monkeypatch.setattr(HttpService, "get", AsyncMock(return_value=html))
    create_page = AsyncMock(return_value="https://telegra.ph/offline")
    monkeypatch.setattr(TelegraphAPI, "create_telegraph_page", create_page)
    answer = AsyncMock()
    monkeypatch.setattr(handler, "answer", answer)
    await handler._process_item(
        FeedItem(1, 2, "https://www.reddit.com/r/offline", "title", "")
    )
    assert create_page.call_args.kwargs["title"] == "Title"
    assert json.loads(create_page.call_args.kwargs["content"]) == [
        {"tag": "p", "children": ["Text ", {"tag": "b", "children": ["bold"]}]}
    ]
    answer.assert_awaited_once()

    parsed = await feed_parser.run(
        RedditFeedItemView._parse_post,
        b'<div class="post"><img alt="Post image" src="image"></div>',
    )
    assert parsed is not None
    assert (parsed.kind, parsed.content) == (
        "image",
        "https://libreddit.qwik.space/image",
    )
