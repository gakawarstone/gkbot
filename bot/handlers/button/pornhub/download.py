from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InaccessibleMessage

from services.ytdlp import YtdlpDownloader
from ui.buttons.pornhub.download import (
    PornhubDownloadButtonData,
    PornhubDownloadButtonDataSerializer,
    PornhubDownloadButtonCallbackDataDeserializer,
    PREFIX,
)


def _get_video_url(ph_video_code: str) -> str:
    return f"https://www.pornhub.com/view_video.php?viewkey={ph_video_code}"


def _is_button_callback(
    callback: CallbackQuery, button_data: PornhubDownloadButtonData
) -> bool:
    if callback.data is None:
        return False

    return callback.data.startswith(
        PornhubDownloadButtonDataSerializer.get_full_prefix(button_data)
    )


async def download(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        return

    deserializer = PornhubDownloadButtonCallbackDataDeserializer()
    if callback.data is None:
        return

    data = deserializer.deserialize(callback.data)
    url = _get_video_url(data.ph_video_code)

    if not data.use_callback_message_as_status:
        status_message = await callback.message.answer("Cкачиваю " + url)
    else:
        status_message = callback.message
        if isinstance(status_message, Message):
            await status_message.edit_text("Cкачиваю " + url)

    if _is_button_callback(callback, PornhubDownloadButtonData.video):
        video = await YtdlpDownloader.download_video(url)
        await callback.message.answer_video(
            video.input_file,
            height=video.height,
            width=video.width,
            duration=video.duration,
            supports_streaming=True,
            has_spoiler=True,
        )

    if isinstance(status_message, Message):
        await status_message.delete()


def setup(r: Router):
    r.callback_query.register(download, F.data.startswith(PREFIX))
