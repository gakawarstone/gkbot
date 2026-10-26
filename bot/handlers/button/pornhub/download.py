from functools import partial

from aiogram import Router
from aiogram.types import CallbackQuery

from handlers.button.download import DownloadRequest, handle_download
from ui.buttons.compatibility import unpack_callback
from ui.buttons.pornhub.download import PornhubDownloadButtonCallbackData


async def _prepare_request(
    callback_data: str, *, data: PornhubDownloadButtonCallbackData | None = None
) -> DownloadRequest:
    if data is None:
        data = unpack_callback(PornhubDownloadButtonCallbackData, callback_data)
    return DownloadRequest(
        url=f"https://www.pornhub.com/view_video.php?viewkey={data.ph_video_code}",
        media_type=data.action.media_type,
        use_callback_message_as_status=data.use_callback_message_as_status,
        video_options={"has_spoiler": True},
    )


async def download(
    callback: CallbackQuery,
    callback_data: PornhubDownloadButtonCallbackData | None = None,
) -> None:
    await handle_download(callback, partial(_prepare_request, data=callback_data))


def setup(r: Router) -> None:
    r.callback_query.register(download, PornhubDownloadButtonCallbackData.filter())
