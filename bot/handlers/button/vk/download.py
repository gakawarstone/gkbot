from typing import Literal

from aiogram import F, Router
from aiogram.types import CallbackQuery

from handlers.button.download import DownloadRequest, handle_download
from ui.buttons.vk import (
    PREFIX,
    VKDownloadButtonCallbackDataDeserializer,
    VKDownloadButtonData,
    VKDownloadButtonDataSerializer,
)


async def _prepare_request(callback_data: str) -> DownloadRequest:
    data = VKDownloadButtonCallbackDataDeserializer.deserialize(callback_data)
    media_type: Literal["audio", "video"] | None = None
    if callback_data.startswith(
        VKDownloadButtonDataSerializer.get_full_prefix(VKDownloadButtonData.audio)
    ):
        media_type = "audio"
    elif callback_data.startswith(
        VKDownloadButtonDataSerializer.get_full_prefix(VKDownloadButtonData.video)
    ):
        media_type = "video"
    return DownloadRequest(
        url=data.reference.download_url,
        media_type=media_type,
        use_callback_message_as_status=data.use_callback_message_as_status,
    )


async def download(callback: CallbackQuery) -> None:
    await handle_download(callback, _prepare_request, raise_on_invalid_callback=True)


def setup(r: Router) -> None:
    r.callback_query.register(download, F.data.startswith(PREFIX))
