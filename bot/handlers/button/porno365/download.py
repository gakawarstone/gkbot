from aiogram import F, Router
from aiogram.types import CallbackQuery

from handlers.button.download import DownloadRequest, handle_download
from services.porno365 import Porno365Service
from ui.buttons.porno365 import (
    PREFIX,
    Porno365DownloadButtonCallbackDataDeserializer,
    Porno365DownloadButtonData,
    Porno365DownloadButtonDataSerializer,
)


async def _prepare_request(callback_data: str) -> DownloadRequest:
    data = Porno365DownloadButtonCallbackDataDeserializer.deserialize(callback_data)
    is_video = callback_data.startswith(
        Porno365DownloadButtonDataSerializer.get_full_prefix(
            Porno365DownloadButtonData.video
        )
    )
    return DownloadRequest(
        url=await Porno365Service.get_best_video_url(data.page_url),
        media_type="video" if is_video else None,
        use_callback_message_as_status=data.use_callback_message_as_status,
        video_options={"has_spoiler": True},
    )


async def download(callback: CallbackQuery) -> None:
    await handle_download(callback, _prepare_request)


def setup(r: Router) -> None:
    r.callback_query.register(download, F.data.startswith(PREFIX))
