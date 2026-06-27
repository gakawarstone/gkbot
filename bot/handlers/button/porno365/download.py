from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from services.porno365 import Porno365Service
from services.ytdlp import YtdlpDownloader
from ui.buttons.porno365 import (
    PREFIX,
    Porno365DownloadButtonCallbackDataDeserializer,
    Porno365DownloadButtonData,
    Porno365DownloadButtonDataSerializer,
)


def _is_button_callback(
    callback: CallbackQuery, button_data: Porno365DownloadButtonData
) -> bool:
    if callback.data is None:
        return False

    return callback.data.startswith(
        Porno365DownloadButtonDataSerializer.get_full_prefix(button_data)
    )


async def download(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        return

    if callback.data is None:
        return

    deserializer = Porno365DownloadButtonCallbackDataDeserializer()
    data = deserializer.deserialize(callback.data)
    url = await Porno365Service.get_best_video_url(data.page_url)

    if not data.use_callback_message_as_status:
        status_message = await callback.message.answer("Cкачиваю " + url)
    else:
        status_message = callback.message
        if isinstance(status_message, Message):
            await status_message.edit_text("Cкачиваю " + url)

    if _is_button_callback(callback, Porno365DownloadButtonData.video):
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
