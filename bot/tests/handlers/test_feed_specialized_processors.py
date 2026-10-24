import json
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

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
from bs4 import BeautifulSoup

from modules.feed.handlers.messages import ShowFeedItemsHandler
from services.gkfeed import FeedItem, GkfeedCredentials
from services.http import HttpRequestError
from services.matreshka import MatreshkaVideo
from services.open_graph import OpenGraphMetadata
from services.tiktok.types import TikTokVideo
from services.youtube import UnavailableVideo, YoutubeVideoData

TOPIC_UUID = "12345678-1234-1234-1234-123456789abc"
IMAGE_URL = "https://example.invalid/image.jpg"
LINKS = {
    "stories": "https://stories.example/video.mp4",
    "vk": "https://vk.com/wall-42_99",
    "youtube": "https://www.youtube.com/watch?v=video-code",
    "reddit": "https://www.reddit.com/r/test/comments/post",
    "tiktok": "https://www.tiktok.com/@author/video/1",
    "pornhub": "https://www.pornhub.com/view_video.php?viewkey=ph-code",
    "porno365": "http://porno365.broker/watch/1",
    "instagram": "https://instagram.com/p/post",
    "sasflix": f"https://sasflix.ru/topics/{TOPIC_UUID}",
    "matreshka": "https://matreshka.tv/video/video-id",
}
CALLBACKS = {
    "vk": ["vkbtn:dlmp3:False:video-42_99", "vkbtn:dlmp4:False:video-42_99"],
    "youtube": ["ytbtn:dlmp3:False:video-code", "ytbtn:dlmp4:False:video-code"],
    "pornhub": ["phbtn:dlmp4:False:ph-code"],
    "porno365": ["p365btn:dlmp4:False:http://porno365.broker/watch/1"],
    "sasflix": [f"sasflixbtn:{TOPIC_UUID}"],
    "matreshka": ["matreshkabtn:video-id"],
}
METADATA = OpenGraphMetadata(IMAGE_URL, "Preview - Publisher", "Description", None)
VK_HTML = (
    "<title>Post title | Channel</title>"
    f'<meta property="og:image" content="{IMAGE_URL}">'
    '<meta property="og:video" content="https://vk.com/video_ext.php?oid=-42&amp;id=99">'
)


class SpecializedHandler(ShowFeedItemsHandler):
    @property
    async def _gkfeed_credentials(self) -> GkfeedCredentials:
        return GkfeedCredentials(login="test", password="test")


@pytest.fixture(params=[Message, CallbackQuery], ids=["message", "callback"])
def event(request: pytest.FixtureRequest) -> MagicMock:
    event = MagicMock(spec=request.param)
    event.from_user = MagicMock(id=7)
    for method in ("answer", "answer_photo", "answer_video"):
        setattr(event, method, AsyncMock())
    if request.param is CallbackQuery:
        event.message = MagicMock(spec=Message)
        for method in ("answer", "answer_photo", "answer_video"):
            setattr(event.message, method, getattr(event, method))
    return event


@pytest.fixture
def bot() -> MagicMock:
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def handler(event: MagicMock, bot: MagicMock) -> SpecializedHandler:
    return SpecializedHandler(event=event, bot=bot)


@pytest.fixture
def item() -> FeedItem:
    return FeedItem(
        id=11,
        feed_id=22,
        link=LINKS["instagram"],
        title="user:Instagram caption",
        text='<img src="data:image/png;base64,cGhvdG8=">',
    )


@pytest.fixture
def services(monkeypatch: pytest.MonkeyPatch) -> dict[str, AsyncMock]:
    mocks = {
        "metadata": AsyncMock(return_value=METADATA),
        "vk_soup": AsyncMock(return_value=BeautifulSoup(VK_HTML, "html.parser")),
        "youtube": AsyncMock(
            return_value=YoutubeVideoData("YT title", "Channel", IMAGE_URL)
        ),
        "tiktok": AsyncMock(
            return_value=TikTokVideo(
                BufferedInputFile(b"video", "tiktok.mp4"),
                height=720,
                width=1280,
                duration=30,
            )
        ),
        "sasflix": AsyncMock(),
        "matreshka": AsyncMock(
            return_value=MatreshkaVideo(
                "video-id",
                "Matreshka title",
                30,
                IMAGE_URL,
                "https://example.invalid/master.m3u8",
            )
        ),
        "raw": AsyncMock(
            return_value={"feed": {"url": "https://stories.example/author"}}
        ),
        "http": AsyncMock(return_value=b"media"),
        "redirect": AsyncMock(return_value="https://example.invalid/video.mp4"),
        "telegraph": AsyncMock(return_value="https://telegra.ph/post"),
    }
    targets = {
        "metadata": "services.open_graph.OpenGraphService.get",
        "vk_soup": "services.open_graph.OpenGraphService.get_soup",
        "youtube": "services.youtube.YoutubeApiService.get_video_data",
        "tiktok": "services.tiktok.TikTokService.get_video",
        "sasflix": "services.sasflix.SasflixService.get_audio",
        "matreshka": "services.matreshka.MatreshkaService.get_video",
        "raw": "services.gkfeed.GkfeedApi.get_raw_item_data",
        "http": "services.http.HttpService.get",
        "redirect": "services.http.HttpService.get_redirected_url",
        "telegraph": "services.telegraph.TelegraphAPI.create_telegraph_page",
    }
    for name, target in targets.items():
        monkeypatch.setattr(target, mocks[name])
    return mocks


def payload_rows(markup: InlineKeyboardMarkup) -> list[list[str | None]]:
    return [
        [button.callback_data or button.url for button in row]
        for row in markup.inline_keyboard
    ]


def assert_plain_link(bot: MagicMock, item: FeedItem) -> None:
    caption = {
        "youtube": "youtube",
        "pornhub": "pornhub",
        "porno365": "porno365",
        "sasflix": "sasflix",
        "matreshka": "matreshka",
        "stories": "stories",
        "reddit": "reddit",
        "instagram": "instagram",
        "tiktok": "TikTok:author",
    }
    source = next(source for source, link in LINKS.items() if item.link == link)
    bot.send_message.assert_awaited_once()
    assert bot.send_message.call_args.args == (
        7,
        f'<a href="{item.link}">{caption[source]}</a>',
    )
    assert payload_rows(bot.send_message.call_args.kwargs["reply_markup"]) == [
        ["fd:show_all_feed:22"],
        ["fd:keep:11", "fd:del:11"],
    ]


@pytest.mark.parametrize("source", LINKS)
async def test_specialized_render_keeps_media_and_keyboard(
    handler: SpecializedHandler,
    item: FeedItem,
    source: str,
    services: dict[str, AsyncMock],
    event: MagicMock,
    bot: MagicMock,
) -> None:
    item = replace(item, link=LINKS[source])
    await handler._process_item(item)
    bot.send_message.assert_not_awaited()
    event.answer.assert_not_awaited()
    sender = (
        event.answer_video if source in {"stories", "tiktok"} else event.answer_photo
    )
    sender.assert_awaited_once()
    media = sender.call_args.args[0]
    kwargs = sender.call_args.kwargs
    markup = kwargs["reply_markup"]
    if source in CALLBACKS:
        assert payload_rows(markup) == [CALLBACKS[source], ["fd:keep:11", "fd:del:11"]]
    else:
        assert payload_rows(markup) == [
            ["fd:show_all_feed:22"],
            ["fd:keep:11", "fd:del:11"],
        ]
    captions = {
        "stories": "author",
        "vk": "Channel",
        "youtube": "Channel",
        "reddit": "r/test",
        "tiktok": "author",
        "pornhub": "Publisher",
        "porno365": "porno365",
        "sasflix": "Sasflix",
        "matreshka": "МатрёшкаТВ",
    }
    expected_caption = (
        "Instagram caption"
        if source == "instagram"
        else f'<a href="{item.link}">{captions[source]}</a>'
    )
    assert expected_caption in kwargs["caption"]
    titles = {
        "vk": "Post title",
        "youtube": "YT title",
        "pornhub": "Preview",
        "porno365": "Preview - Publisher",
        "sasflix": "Preview - Publisher",
        "matreshka": "Matreshka title",
    }
    if source in titles:
        assert kwargs["caption"] == f"<b>{titles[source]}</b>\n\n{expected_caption}"
    if source in {"vk", "pornhub", "porno365", "sasflix", "matreshka"}:
        assert isinstance(media, URLInputFile)
        assert media.url == IMAGE_URL
        assert kwargs["has_spoiler"] is (source in {"pornhub", "porno365"})
    if source == "instagram":
        assert isinstance(media, BufferedInputFile)
        assert media.data == b"photo"
    if source == "reddit":
        assert isinstance(media, BufferedInputFile)
        assert media.data == b"media"
    if source == "tiktok":
        assert isinstance(media, BufferedInputFile)
        assert media.data == b"video"
        assert (kwargs["height"], kwargs["width"], kwargs["duration"]) == (
            720,
            1280,
            30,
        )
        assert kwargs["supports_streaming"] is True
    if source == "stories":
        assert isinstance(media, BufferedInputFile)
        assert media.data == b"media"


async def test_vk_text_preserves_line_breaks_and_feed_actions(
    handler: SpecializedHandler,
    item: FeedItem,
    services: dict[str, AsyncMock],
    event: MagicMock,
) -> None:
    html = '<title>Post title | Channel</title><meta property="og:description" content="Line1&lt;br&gt;Line2">'
    services["vk_soup"].return_value = BeautifulSoup(html, "html.parser")
    await handler._process_item(replace(item, link=LINKS["vk"]))
    assert payload_rows(event.answer.call_args.kwargs["reply_markup"]) == [
        ["fd:show_all_feed:22"],
        ["fd:keep:11", "fd:del:11"],
    ]
    assert event.answer.call_args.args[0] == (
        f"<b>Line1\nLine2</b>\n\n<a href='{LINKS['vk']}'>Channel</a>"
    )


@pytest.mark.parametrize("branch", ["image", "video", "link", "gallery", "missing"])
async def test_reddit_alternate_branches(
    handler: SpecializedHandler,
    item: FeedItem,
    services: dict[str, AsyncMock],
    event: MagicMock,
    bot: MagicMock,
    branch: str,
) -> None:
    services["metadata"].side_effect = HttpRequestError()
    contents = {
        "image": '<img alt="Post image" src="image.jpg">',
        "video": '<meta property="og:video" content="https://example.invalid/video.mp4">',
        "link": '<a id="post_url" href="https://example.invalid/article">link</a>',
        "gallery": '<div class="post_body">body</div><div class="gallery"><img src="gallery.jpg"></div>',
        "missing": "",
    }
    html = "<title>Post title - r/test</title>"
    if branch != "missing":
        html += f'<div class="post">{contents[branch]}</div>'
    services["http"].side_effect = [html.encode(), b"video"]
    await handler._process_item(replace(item, link=LINKS["reddit"]))
    if branch == "missing":
        assert_plain_link(bot, replace(item, link=LINKS["reddit"]))
        event.answer.assert_not_awaited()
        return
    bot.send_message.assert_not_awaited()
    if branch == "image":
        photo = event.answer_photo.call_args.args[0]
        assert isinstance(photo, URLInputFile)
        assert photo.url == "https://libreddit.qwik.space/image.jpg"
    elif branch == "video":
        video = event.answer_video.call_args.args[0]
        assert isinstance(video, BufferedInputFile)
        assert video.data == b"video"
    else:
        markup = event.answer.call_args.kwargs["reply_markup"]
        expected_url = (
            "https://example.invalid/article"
            if branch == "link"
            else "https://telegra.ph/post"
        )
        assert payload_rows(markup) == [[expected_url], ["fd:keep:11", "fd:del:11"]]
        if branch == "gallery":
            assert json.loads(services["telegraph"].call_args.kwargs["content"]) == [
                {
                    "tag": "img",
                    "attrs": {"src": "gallery.jpg"},
                }
            ]


@pytest.mark.parametrize(
    "source", ["pornhub", "porno365", "sasflix", "matreshka", "youtube"]
)
async def test_source_local_fallbacks(
    handler: SpecializedHandler,
    item: FeedItem,
    services: dict[str, AsyncMock],
    source: str,
    bot: MagicMock,
    event: MagicMock,
) -> None:
    services["metadata"].return_value = replace(METADATA, image_url=None)
    services["matreshka"].return_value = replace(
        services["matreshka"].return_value, image_url=None
    )
    services["youtube"].side_effect = UnavailableVideo(LINKS["youtube"])
    item = replace(item, link=LINKS[source])
    await handler._process_item(item)
    assert_plain_link(bot, item)
    event.answer_photo.assert_not_awaited()


async def test_pornhub_without_viewkey_keeps_feed_actions(
    handler: SpecializedHandler,
    item: FeedItem,
    services: dict[str, AsyncMock],
    event: MagicMock,
) -> None:
    await handler._process_item(replace(item, link="https://www.pornhub.com/no-key"))
    assert payload_rows(event.answer_photo.call_args.kwargs["reply_markup"]) == [
        ["fd:keep:11", "fd:del:11"]
    ]


@pytest.mark.parametrize("source", ["stories", "reddit"])
async def test_recoverable_source_failures_use_generic_response_once(
    handler: SpecializedHandler,
    item: FeedItem,
    services: dict[str, AsyncMock],
    source: str,
    bot: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    for mock in services.values():
        mock.side_effect = HttpRequestError("private-url")
    item = replace(item, link=LINKS[source])
    await handler._process_item(item)
    assert_plain_link(bot, item)
    assert "private-url" not in caplog.text


@pytest.mark.parametrize("source", ["youtube", "tiktok", "instagram", "reddit"])
async def test_media_send_failure_preserves_generic_response(
    handler: SpecializedHandler,
    item: FeedItem,
    services: dict[str, AsyncMock],
    source: str,
    bot: MagicMock,
    event: MagicMock,
) -> None:
    error = TelegramBadRequest(SendPhoto(chat_id=7, photo="image"), "invalid media")
    event.answer_photo.side_effect = error
    event.answer_video.side_effect = error
    item = replace(item, link=LINKS[source])
    await handler._process_item(item)
    assert_plain_link(bot, item)
