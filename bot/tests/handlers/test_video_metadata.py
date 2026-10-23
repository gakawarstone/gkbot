from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import SendVideo
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from handlers.text.ytdlp_short import YtdlpShortVideoHandler
from modules.feed.handlers.views.tiktok import TikTokFeedItemView
from services.gkfeed import FeedItem
from services.porno365 import Porno365Service
from services.tiktok import TikTokService
from services.tiktok.types import TikTokVideo
from services.video import VideoMetadata
from services.youtube import YoutubeApiService
from services.ytdlp import YtdlpDownloader
from services.ytdlp._types import VideoFileInfo
from ui.video import send_video


class FeedVideoHandler(TikTokFeedItemView):
    async def handle(self) -> None:
        pass


@pytest.mark.parametrize("with_metadata", [False, True])
@pytest.mark.parametrize("callback", [False, True])
async def test_feed_video_send_arguments(
    monkeypatch: pytest.MonkeyPatch, with_metadata: bool, callback: bool
) -> None:
    file = BufferedInputFile(b"video", "video.mp4")
    video = TikTokVideo(file, height=720, width=1280, duration=60)
    if with_metadata:
        video.cover = "https://example.com/cover.jpg"
        video.start_timestamp = 12
    monkeypatch.setattr(TikTokService, "get_video", AsyncMock(return_value=video))
    message = MagicMock(spec=Message)
    message.answer_video = AsyncMock()
    event = MagicMock(spec=CallbackQuery) if callback else message
    if callback:
        event.message = message
    handler = FeedVideoHandler(event=event)
    item = FeedItem(1, 2, "https://www.tiktok.com/@user/video/1", "title", "text")
    await handler._process_tiktok_item(item)
    args, kwargs = message.answer_video.await_args
    assert args == (file,)
    assert kwargs["caption"] == f'<a href="{item.link}">user</a>'
    assert (kwargs["height"], kwargs["width"], kwargs["duration"]) == (720, 1280, 60)
    assert kwargs["supports_streaming"] is True
    assert kwargs["reply_markup"] is not None
    assert {
        key: kwargs[key] for key in ("cover", "start_timestamp") if key in kwargs
    } == ({"cover": video.cover, "start_timestamp": 12} if with_metadata else {})
    # Validate the arguments against the installed aiogram schema as well.
    SendVideo(chat_id=123, video=file, **kwargs)


@pytest.mark.parametrize("with_metadata", [False, True])
async def test_short_download_handler_passes_metadata(
    monkeypatch: pytest.MonkeyPatch, with_metadata: bool
) -> None:
    file = BufferedInputFile(b"video", "video.mp4")
    video = VideoFileInfo(file, 720, 1280, 60, "title")
    if with_metadata:
        video.cover = "https://example.com/cover.jpg"
        video.start_timestamp = 12

    @asynccontextmanager
    async def download(url: str) -> AsyncIterator[VideoFileInfo]:
        yield video

    monkeypatch.setattr(YtdlpDownloader, "download_video", download)
    event = MagicMock(spec=Message)
    event.text = "https://www.youtube.com/shorts/id?t=12"
    event.from_user = SimpleNamespace(username="user")
    event.chat = SimpleNamespace(id=123)
    event.delete = AsyncMock()
    event.answer_video = AsyncMock()
    status = SimpleNamespace(delete=AsyncMock())
    event.answer = AsyncMock(return_value=status)
    event.bot = SimpleNamespace(send_chat_action=AsyncMock())
    await YtdlpShortVideoHandler(event=event, bot=event.bot).handle()
    args, kwargs = event.answer_video.await_args
    assert args == (file,)
    assert kwargs["caption"] == f"<b>user</b> {event.text}"
    assert kwargs["duration"] == 60
    assert kwargs.get("cover") == video.cover
    assert kwargs.get("start_timestamp") == video.start_timestamp
    if not with_metadata:
        assert "cover" not in kwargs
        assert "start_timestamp" not in kwargs
    status.delete.assert_awaited_once_with()


async def test_rejected_metadata_retries_original_arguments() -> None:
    file = BufferedInputFile(b"video", "video.mp4")
    thumbnail = BufferedInputFile(b"thumbnail", "thumbnail.jpg")
    method = SendVideo(chat_id=123, video=file)
    error = TelegramBadRequest(method, "Bad Request: failed to get HTTP URL content")
    message = MagicMock(spec=Message)
    sender = AsyncMock(side_effect=[error, message])
    metadata = VideoMetadata(cover="https://example.com/cover.jpg", start_timestamp=12)
    kwargs = {
        "caption": "caption",
        "duration": 60,
        "thumbnail": thumbnail,
        "has_spoiler": True,
    }
    assert await send_video(sender, file, metadata=metadata, **kwargs) is message
    assert sender.await_count == 2
    assert sender.await_args_list[0].kwargs == dict(
        kwargs, cover=metadata.cover, start_timestamp=12
    )
    assert sender.await_args_list[1].args == (file,)
    assert sender.await_args_list[1].kwargs == kwargs


@pytest.mark.parametrize("network_error", [False, True])
async def test_send_errors_are_not_retried_without_metadata_or_on_network_failure(
    network_error: bool,
) -> None:
    method = SendVideo(chat_id=123, video="video-id")
    error_type = TelegramNetworkError if network_error else TelegramBadRequest
    error = error_type(method, "send failed")
    sender = AsyncMock(side_effect=error)
    metadata = (
        VideoMetadata(cover="https://example.com/cover.jpg") if network_error else None
    )
    with pytest.raises(error_type) as raised:
        await send_video(sender, "video-id", metadata=metadata)
    assert raised.value is error
    sender.assert_awaited_once()


async def test_retry_is_bounded_and_invalid_metadata_is_omitted() -> None:
    method = SendVideo(chat_id=123, video="video-id")
    error = TelegramBadRequest(method, "send failed")
    sender = AsyncMock(side_effect=error)
    with pytest.raises(TelegramBadRequest):
        await send_video(sender, "video-id", metadata=VideoMetadata(start_timestamp=12))
    assert sender.await_count == 2
    sender.reset_mock()
    sender.side_effect = None
    await send_video(
        sender,
        "video-id",
        metadata=VideoMetadata(cover="file:///tmp/cover.jpg", start_timestamp=-1),
    )
    sender.assert_awaited_once_with("video-id")


@pytest.mark.parametrize(
    ("provider", "callback_data"),
    [
        ("youtube", "ytbtn:dlmp4:False:video-id"),
        ("vk", "vkbtn:dlmp4:False:-1_2"),
        ("pornhub", "phbtn:dlmp4:False:video-id"),
        ("porno365", "p365btn:dlmp4:False:https://example.com/page"),
    ],
)
async def test_button_handlers_keep_existing_send_options(
    monkeypatch: pytest.MonkeyPatch, provider: str, callback_data: str
) -> None:
    module = import_module(f"handlers.button.{provider}.download")
    file = BufferedInputFile(b"video", "video.mp4")
    video = VideoFileInfo(
        file,
        720,
        1280,
        60,
        "title",
        cover="https://example.com/cover.jpg",
        start_timestamp=12,
    )

    @asynccontextmanager
    async def download(url: str) -> AsyncIterator[VideoFileInfo]:
        yield video

    monkeypatch.setattr(YtdlpDownloader, "download_video", download)
    monkeypatch.setattr(
        YoutubeApiService,
        "get_video_data",
        AsyncMock(
            return_value=SimpleNamespace(
                channel_title="channel",
                thumbnail_url="https://example.com/thumbnail.jpg",
            )
        ),
    )
    monkeypatch.setattr(
        Porno365Service,
        "get_best_video_url",
        AsyncMock(return_value="https://example.com/video.mp4"),
    )
    message = MagicMock(spec=Message)
    message.answer_video = AsyncMock()
    status = MagicMock(spec=Message)
    status.delete = AsyncMock()
    message.answer = AsyncMock(return_value=status)
    callback = MagicMock(spec=CallbackQuery)
    callback.message = message
    callback.data = callback_data
    await module.download(callback)
    args, kwargs = message.answer_video.await_args
    assert args == (file,)
    assert kwargs["cover"] == video.cover
    assert kwargs["start_timestamp"] == 12
    assert (kwargs["height"], kwargs["width"], kwargs["duration"]) == (720, 1280, 60)
    assert kwargs["supports_streaming"] is True
    if provider == "youtube":
        assert kwargs["thumbnail"].url == "https://example.com/thumbnail.jpg"
        assert (
            kwargs["caption"]
            == '<b>title</b>\n\n<a href="https://www.youtube.com/watch?v=video-id">channel</a>'
        )
    if provider in {"pornhub", "porno365"}:
        assert kwargs["has_spoiler"] is True
    status.delete.assert_awaited_once_with()
