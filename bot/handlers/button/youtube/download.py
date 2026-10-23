from aiogram import F, Router
from aiogram.types import CallbackQuery, URLInputFile

from handlers.button.download import (
    DownloadRequest,
    VideoOptions,
    get_media_type,
)
from handlers.button.download import (
    download as download_media,
)
from services.youtube import YoutubeApiService
from services.ytdlp._types import VideoFileInfo
from ui.buttons.youtube.download import (
    PREFIX,
    YoutubeDownloadButtonCallbackDataDeserializer,
    YoutubeDownloadButtonData,
    YoutubeDownloadButtonDataSerializer,
)
from utils.strings import remove_emoji


async def _prepare_request(callback_data: str) -> DownloadRequest:
    data = YoutubeDownloadButtonCallbackDataDeserializer.deserialize(callback_data)
    return DownloadRequest(
        url="https://www.youtube.com/watch?v=" + data.yt_video_code,
        use_callback_message_as_status=data.use_callback_message_as_status,
        media_type=get_media_type(
            callback_data,
            video_prefix=YoutubeDownloadButtonDataSerializer.get_full_prefix(
                YoutubeDownloadButtonData.video
            ),
            audio_prefix=YoutubeDownloadButtonDataSerializer.get_full_prefix(
                YoutubeDownloadButtonData.audio
            ),
        ),
    )


async def _video_options(url: str, video: VideoFileInfo) -> VideoOptions:
    data = await YoutubeApiService.get_video_data(url)
    channel_title = remove_emoji(data.channel_title)
    return {
        "caption": f'<b>{video.title}</b>\n\n<a href="{url}">{channel_title}</a>',
        "thumbnail": URLInputFile(data.thumbnail_url),
    }


async def download(callback: CallbackQuery) -> None:
    await download_media(
        callback,
        prepare_request=_prepare_request,
        video_options=_video_options,
    )


def setup(r: Router) -> None:
    r.callback_query.register(download, F.data.startswith(PREFIX))
