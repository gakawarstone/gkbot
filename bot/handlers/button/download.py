"""Shared lifecycle for download callbacks; sources keep their legacy payloads."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal

from aiogram.types import CallbackQuery, InaccessibleMessage, InputFile

from services.ytdlp import YtdlpDownloader
from services.ytdlp._types import VideoFileInfo
from ui.video import send_video

type MediaType = Literal["audio", "video"]


@dataclass(frozen=True)
class DownloadRequest:
    url: str
    use_callback_message_as_status: bool
    media_type: MediaType | None


@dataclass(frozen=True)
class VideoOptions:
    caption: str | None = None
    thumbnail: InputFile | None = None
    has_spoiler: bool | None = None


def get_media_type(
    callback_data: str, *, video_prefix: str, audio_prefix: str | None = None
) -> MediaType | None:
    if audio_prefix is not None and callback_data.startswith(audio_prefix):
        return "audio"
    if callback_data.startswith(video_prefix):
        return "video"
    return None


async def download(
    callback: CallbackQuery,
    *,
    prepare_request: Callable[[str], Awaitable[DownloadRequest]],
    video_options: Callable[[str, VideoFileInfo], Awaitable[VideoOptions]]
    | None = None,
    require_callback: bool = False,
) -> None:
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        if require_callback:
            raise ValueError("Callback message is inaccessible or None")
        return
    if callback.data is None:
        if require_callback:
            raise ValueError("Callback data cannot be None")
        return

    request = await prepare_request(callback.data)
    message = callback.message
    if request.use_callback_message_as_status:
        status_message = message
    else:
        status_message = await message.answer("Cкачиваю " + request.url)

    try:
        if request.use_callback_message_as_status:
            await status_message.edit_text("Cкачиваю " + request.url)

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
                options = (
                    await video_options(request.url, video)
                    if video_options
                    else VideoOptions()
                )
                await send_video(
                    message.answer_video,
                    video.input_file,
                    metadata=video,
                    height=video.height,
                    width=video.width,
                    duration=video.duration,
                    supports_streaming=True,
                    caption=options.caption,
                    thumbnail=options.thumbnail,
                    has_spoiler=options.has_spoiler,
                )
    finally:
        await status_message.delete()
