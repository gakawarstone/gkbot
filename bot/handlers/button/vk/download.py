from aiogram import F, Router
from aiogram.types import CallbackQuery

from handlers.button.download import (
    DownloadRequest,
    get_media_type,
)
from handlers.button.download import (
    download as download_media,
)
from ui.buttons.vk import (
    PREFIX,
    VKDownloadButtonCallbackDataDeserializer,
    VKDownloadButtonData,
    VKDownloadButtonDataSerializer,
)
from utils.vk import reconstruct_vk_url


async def _prepare_request(callback_data: str) -> DownloadRequest:
    data = VKDownloadButtonCallbackDataDeserializer.deserialize(callback_data)
    return DownloadRequest(
        url=reconstruct_vk_url(data.vk_id),
        use_callback_message_as_status=data.use_callback_message_as_status,
        media_type=get_media_type(
            callback_data,
            video_prefix=VKDownloadButtonDataSerializer.get_full_prefix(
                VKDownloadButtonData.video
            ),
            audio_prefix=VKDownloadButtonDataSerializer.get_full_prefix(
                VKDownloadButtonData.audio
            ),
        ),
    )


async def download(callback: CallbackQuery) -> None:
    await download_media(
        callback,
        prepare_request=_prepare_request,
        require_callback=True,
    )


def setup(r: Router) -> None:
    r.callback_query.register(download, F.data.startswith(PREFIX))
