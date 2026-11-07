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
from services.porno365 import Porno365Service
from services.ytdlp._types import VideoFileInfo
from ui.buttons.porno365 import (
    PREFIX,
    Porno365DownloadButtonCallbackDataDeserializer,
    Porno365DownloadButtonData,
    Porno365DownloadButtonDataSerializer,
)


async def _prepare_request(callback_data: str) -> DownloadRequest:
    data = Porno365DownloadButtonCallbackDataDeserializer.deserialize(callback_data)
    return DownloadRequest(
        url=await Porno365Service.get_best_video_url(data.page_url),
        use_callback_message_as_status=data.use_callback_message_as_status,
        media_type=get_media_type(
            callback_data,
            video_prefix=Porno365DownloadButtonDataSerializer.get_full_prefix(
                Porno365DownloadButtonData.video
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
