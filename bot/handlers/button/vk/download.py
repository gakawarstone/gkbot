from functools import partial

from aiogram import Router
from aiogram.types import CallbackQuery

from handlers.button.download import DownloadRequest, handle_download
from ui.buttons.compatibility import LegacyDownloadCallbackFilter, unpack_callback
from ui.buttons.vk import VKDownloadButtonCallbackData


async def _prepare_request(
    callback_data: str, *, data: VKDownloadButtonCallbackData | None = None
) -> DownloadRequest:
    if data is None:
        data = unpack_callback(VKDownloadButtonCallbackData, callback_data)
    return DownloadRequest(
        url=data.reference.download_url,
        media_type=data.action.media_type,
        use_callback_message_as_status=data.use_callback_message_as_status,
    )


async def download(
    callback: CallbackQuery,
    callback_data: VKDownloadButtonCallbackData | None = None,
) -> None:
    await handle_download(
        callback,
        partial(_prepare_request, data=callback_data),
        raise_on_invalid_callback=True,
    )


def setup(r: Router) -> None:
    r.callback_query.register(download, VKDownloadButtonCallbackData.filter())
    r.callback_query.register(
        download, LegacyDownloadCallbackFilter(VKDownloadButtonCallbackData)
    )
