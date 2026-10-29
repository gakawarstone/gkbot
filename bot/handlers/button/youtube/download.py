from aiogram import Router
from aiogram.types import CallbackQuery, URLInputFile

from handlers.button.download import DownloadRequest, VideoOptions, handle_download
from services.youtube import YoutubeApiService
from services.ytdlp._types import VideoFileInfo
from ui.buttons.youtube.download import YoutubeDownloadButtonCallbackData
from utils.strings import remove_emoji


async def _prepare_video(url: str, video: VideoFileInfo) -> VideoOptions:
    data = await YoutubeApiService.get_video_data(url)
    channel_title = remove_emoji(data.channel_title)
    return {
        "caption": f'<b>{video.title}</b>\n\n<a href="{url}">{channel_title}</a>',
        "thumbnail": URLInputFile(data.thumbnail_url),
    }


async def download(
    callback: CallbackQuery,
    callback_data: YoutubeDownloadButtonCallbackData | None = None,
) -> None:
    async def prepare_request(payload: str) -> DownloadRequest:
        data = (
            callback_data
            if callback_data is not None
            else YoutubeDownloadButtonCallbackData.unpack(payload)
        )
        return DownloadRequest(
            url="https://www.youtube.com/watch?v=" + data.yt_video_code,
            media_type=data.action.media_type,
            use_callback_message_as_status=data.use_callback_message_as_status,
            prepare_video=_prepare_video,
        )

    await handle_download(callback, prepare_request)


def setup(r: Router) -> None:
    r.callback_query.register(download, YoutubeDownloadButtonCallbackData.filter())
