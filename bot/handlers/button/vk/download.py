from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InaccessibleMessage

from services.ytdlp import YtdlpDownloader
from ui.buttons.vk import (
    VKDownloadButtonData,
    VKDownloadButtonCallbackDataDeserializer,
    VKDownloadButtonDataSerializer,
    PREFIX,
)


def _is_button_callback(
    callback: CallbackQuery, button_data: VKDownloadButtonData
) -> bool:
    if callback.data is None:
        raise ValueError("Callback data cannot be None")

    return callback.data.startswith(
        VKDownloadButtonDataSerializer.get_full_prefix(button_data)
    )


async def download(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        raise ValueError("Callback message is inaccessible or None")

    deserializer = VKDownloadButtonCallbackDataDeserializer()
    if callback.data is None:
        raise ValueError("Callback data cannot be None")

    data = deserializer.deserialize(callback.data)

    if not data.use_callback_message_as_status:
        status_message = await callback.message.answer("Cкачиваю " + data.url)
    else:
        status_message = callback.message
        if isinstance(status_message, Message):
            await status_message.edit_text("Cкачиваю " + data.url)

    if _is_button_callback(callback, VKDownloadButtonData.audio):
        audio = await YtdlpDownloader.download_audio(data.url)
        await callback.message.answer_audio(
            audio=audio.input_file,
            title=audio.title,
            performer="GKBOT",
            duration=audio.duration,
        )

    if _is_button_callback(callback, VKDownloadButtonData.video):
        video = await YtdlpDownloader.download_video(data.url)
        await callback.message.answer_video(
            video.input_file,
            height=video.height,
            width=video.width,
            duration=video.duration,
            supports_streaming=True,
        )

    if isinstance(status_message, Message):
        await status_message.delete()


def setup(r: Router):
    r.callback_query.register(download, F.data.startswith(PREFIX))

