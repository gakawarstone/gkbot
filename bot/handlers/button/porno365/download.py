from aiogram import Router
from aiogram.types import CallbackQuery

from handlers.button.download import DownloadRequest, handle_download
from services.porno365 import Porno365Service
from ui.buttons.compatibility import LegacyDownloadCallbackFilter, unpack_callback
from ui.buttons.porno365 import Porno365DownloadButtonCallbackData


async def download(
    callback: CallbackQuery,
    callback_data: Porno365DownloadButtonCallbackData | None = None,
) -> None:
    async def prepare_request(payload: str) -> DownloadRequest:
        data = (
            callback_data
            if callback_data is not None
            else unpack_callback(Porno365DownloadButtonCallbackData, payload)
        )
        return DownloadRequest(
            url=await Porno365Service.get_best_video_url(data.page_url),
            media_type=data.action.media_type,
            use_callback_message_as_status=data.use_callback_message_as_status,
            video_options={"has_spoiler": True},
        )

    await handle_download(callback, prepare_request)


def setup(r: Router) -> None:
    r.callback_query.register(download, Porno365DownloadButtonCallbackData.filter())
    r.callback_query.register(
        download, LegacyDownloadCallbackFilter(Porno365DownloadButtonCallbackData)
    )
