from aiogram import F, Router
from aiogram.types import CallbackQuery

from handlers.button.download import DownloadRequest, handle_download
from ui.buttons.pornhub.download import (
    PREFIX,
    PornhubDownloadButtonCallbackDataDeserializer,
    PornhubDownloadButtonData,
    PornhubDownloadButtonDataSerializer,
)


async def _prepare_request(callback_data: str) -> DownloadRequest:
    data = PornhubDownloadButtonCallbackDataDeserializer.deserialize(callback_data)
    is_video = callback_data.startswith(
        PornhubDownloadButtonDataSerializer.get_full_prefix(
            PornhubDownloadButtonData.video
        )
    )
    return DownloadRequest(
        url=f"https://www.pornhub.com/view_video.php?viewkey={data.ph_video_code}",
        media_type="video" if is_video else None,
        use_callback_message_as_status=data.use_callback_message_as_status,
        video_options={"has_spoiler": True},
    )


async def download(callback: CallbackQuery) -> None:
    await handle_download(callback, _prepare_request)


def setup(r: Router) -> None:
    r.callback_query.register(download, F.data.startswith(PREFIX))
