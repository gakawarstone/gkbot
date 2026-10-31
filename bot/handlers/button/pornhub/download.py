from aiogram import F, Router
from aiogram.types import CallbackQuery

from handlers.button.download import (
    DownloadRequest,
    VideoOptions,
    get_media_type,
)
from handlers.button.download import (
    download as download_media,
)
from services.ytdlp._types import VideoFileInfo
from ui.buttons.pornhub.download import (
    PREFIX,
    PornhubDownloadButtonCallbackDataDeserializer,
    PornhubDownloadButtonData,
    PornhubDownloadButtonDataSerializer,
)


async def _prepare_request(callback_data: str) -> DownloadRequest:
    data = PornhubDownloadButtonCallbackDataDeserializer.deserialize(callback_data)
    return DownloadRequest(
        url=f"https://www.pornhub.com/view_video.php?viewkey={data.ph_video_code}",
        use_callback_message_as_status=data.use_callback_message_as_status,
        media_type=get_media_type(
            callback_data,
            video_prefix=PornhubDownloadButtonDataSerializer.get_full_prefix(
                PornhubDownloadButtonData.video
            ),
        ),
    )


async def _video_options(url: str, video: VideoFileInfo) -> VideoOptions:
    return {"has_spoiler": True}


async def download(callback: CallbackQuery) -> None:
    await download_media(
        callback,
        prepare_request=_prepare_request,
        video_options=_video_options,
    )


def setup(r: Router) -> None:
    r.callback_query.register(download, F.data.startswith(PREFIX))
