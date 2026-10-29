from aiogram import Router
from aiogram.types import CallbackQuery

from handlers.button.download import DownloadRequest, handle_download
from ui.buttons.pornhub.download import PornhubDownloadButtonCallbackData


async def download(
    callback: CallbackQuery,
    callback_data: PornhubDownloadButtonCallbackData | None = None,
) -> None:
    async def prepare_request(payload: str) -> DownloadRequest:
        data = (
            callback_data
            if callback_data is not None
            else PornhubDownloadButtonCallbackData.unpack(payload)
        )
        return DownloadRequest(
            url=f"https://www.pornhub.com/view_video.php?viewkey={data.ph_video_code}",
            media_type=data.action.media_type,
            use_callback_message_as_status=data.use_callback_message_as_status,
            video_options={"has_spoiler": True},
        )

    await handle_download(callback, prepare_request)


def setup(r: Router) -> None:
    r.callback_query.register(download, PornhubDownloadButtonCallbackData.filter())
