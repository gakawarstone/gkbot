"""Shared lifecycle for source-specific download callback adapters."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Literal, TypedDict

from aiogram.types import CallbackQuery, InaccessibleMessage, InputFile, Message

from services.ytdlp import YtdlpDownloader
from services.ytdlp._types import VideoFileInfo


class VideoOptions(TypedDict, total=False):
    caption: str
    thumbnail: InputFile
    has_spoiler: bool


VideoOptionsFactory = Callable[[str, VideoFileInfo], Awaitable[VideoOptions]]


@dataclass(frozen=True)
class DownloadRequest:
    url: str
    media_type: Literal["audio", "video"] | None
    use_callback_message_as_status: bool = False
    video_options: VideoOptions = field(default_factory=VideoOptions)
    prepare_video: VideoOptionsFactory | None = None


DownloadRequestFactory = Callable[[str], Awaitable[DownloadRequest]]


async def handle_download(
    callback: CallbackQuery,
    prepare_request: DownloadRequestFactory,
    *,
    raise_on_invalid_callback: bool = False,
) -> None:
    """Validate a callback and keep status and media cleanup in one place.

    Adapters own payload parsing, URL resolution and optional video metadata.
    A None media type preserves the legacy status-only path for unknown events.
    """
    message = callback.message
    if message is None or isinstance(message, InaccessibleMessage):
        if raise_on_invalid_callback:
            raise ValueError("Callback message is inaccessible or None")
        return
    if callback.data is None:
        if raise_on_invalid_callback:
            raise ValueError("Callback data cannot be None")
        return

    request = await prepare_request(callback.data)
    status_text = "Cкачиваю " + request.url
    if request.use_callback_message_as_status:
        status_message = message
        await status_message.edit_text(status_text)
    else:
        status_message = await message.answer(status_text)

    try:
        await _send_media(message, request)
    finally:
        await status_message.delete()


async def _send_media(message: Message, request: DownloadRequest) -> None:
    if request.media_type == "audio":
        async with YtdlpDownloader.download_audio(request.url) as audio:
            await message.answer_audio(
                audio=audio.input_file,
                title=audio.title,
                performer="GKBOT",
                duration=audio.duration,
            )
    elif request.media_type == "video":
        async with YtdlpDownloader.download_video(request.url) as video:
            options = request.video_options.copy()
            if request.prepare_video is not None:
                options.update(await request.prepare_video(request.url, video))
            await message.answer_video(
                video.input_file,
                height=video.height,
                width=video.width,
                duration=video.duration,
                supports_streaming=True,
                **options,
            )
