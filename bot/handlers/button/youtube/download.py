from typing import Literal

from aiogram import F, Router
from aiogram.types import CallbackQuery, URLInputFile

from handlers.button.download import DownloadRequest, VideoOptions, handle_download
from services.youtube import YoutubeApiService
from services.ytdlp._types import VideoFileInfo
from ui.buttons.youtube.download import (
    PREFIX,
    YoutubeDownloadButtonCallbackDataDeserializer,
    YoutubeDownloadButtonData,
    YoutubeDownloadButtonDataSerializer,
)
from utils.strings import remove_emoji


async def _prepare_video(url: str, video: VideoFileInfo) -> VideoOptions:
    data = await YoutubeApiService.get_video_data(url)
    channel_title = remove_emoji(data.channel_title)
    return {
        "caption": f'<b>{video.title}</b>\n\n<a href="{url}">{channel_title}</a>',
        "thumbnail": URLInputFile(data.thumbnail_url),
    }


async def _prepare_request(callback_data: str) -> DownloadRequest:
    data = YoutubeDownloadButtonCallbackDataDeserializer.deserialize(callback_data)
    media_type: Literal["audio", "video"] | None = None
    if callback_data.startswith(
        YoutubeDownloadButtonDataSerializer.get_full_prefix(
            YoutubeDownloadButtonData.audio
        )
    ):
        media_type = "audio"
    elif callback_data.startswith(
        YoutubeDownloadButtonDataSerializer.get_full_prefix(
            YoutubeDownloadButtonData.video
        )
    ):
        media_type = "video"
    return DownloadRequest(
        url="https://www.youtube.com/watch?v=" + data.yt_video_code,
        media_type=media_type,
        use_callback_message_as_status=data.use_callback_message_as_status,
        prepare_video=_prepare_video,
    )


async def download(callback: CallbackQuery) -> None:
    await handle_download(callback, _prepare_request)


def setup(r: Router) -> None:
    r.callback_query.register(download, F.data.startswith(PREFIX))
