from functools import partial

from aiogram import Router
from aiogram.types import CallbackQuery

from handlers.button.download import DownloadRequest, handle_download
from services.porno365 import Porno365Service
from ui.buttons.compatibility import LegacyDownloadCallbackFilter, unpack_callback
from ui.buttons.porno365 import Porno365DownloadButtonCallbackData


async def _prepare_request(
    callback_data: str, *, data: Porno365DownloadButtonCallbackData | None = None
) -> DownloadRequest:
    if data is None:
        data = unpack_callback(Porno365DownloadButtonCallbackData, callback_data)
    return DownloadRequest(
        url=await Porno365Service.get_best_video_url(data.page_url),
        media_type=data.action.media_type,
        use_callback_message_as_status=data.use_callback_message_as_status,
        video_options={"has_spoiler": True},
    )


async def download(
    callback: CallbackQuery,
    callback_data: Porno365DownloadButtonCallbackData | None = None,
) -> None:
    await handle_download(callback, partial(_prepare_request, data=callback_data))


def setup(r: Router) -> None:
    r.callback_query.register(download, Porno365DownloadButtonCallbackData.filter())
    r.callback_query.register(
        download, LegacyDownloadCallbackFilter(Porno365DownloadButtonCallbackData)
    )
