from aiogram import Router
from aiogram.types import CallbackQuery

from handlers.button.download import DownloadRequest, handle_download
from ui.buttons.compatibility import LegacyDownloadCallbackFilter, unpack_callback
from ui.buttons.vk import VKDownloadButtonCallbackData


async def download(
    callback: CallbackQuery,
    callback_data: VKDownloadButtonCallbackData | None = None,
) -> None:
    async def prepare_request(payload: str) -> DownloadRequest:
        data = (
            callback_data
            if callback_data is not None
            else unpack_callback(VKDownloadButtonCallbackData, payload)
        )
        return DownloadRequest(
            url=data.reference.download_url,
            media_type=data.action.media_type,
            use_callback_message_as_status=data.use_callback_message_as_status,
        )

    await handle_download(callback, prepare_request, raise_on_invalid_callback=True)


def setup(r: Router) -> None:
    r.callback_query.register(download, VKDownloadButtonCallbackData.filter())
    r.callback_query.register(
        download, LegacyDownloadCallbackFilter(VKDownloadButtonCallbackData)
    )
