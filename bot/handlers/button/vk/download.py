from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from services.ytdlp import YtdlpDownloader
from ui.buttons.vk import (
    PREFIX,
    VKDownloadButtonCallbackDataDeserializer,
    VKDownloadButtonData,
    VKDownloadButtonDataSerializer,
)
from ui.video import send_video
from utils.vk import reconstruct_vk_url


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
    url = reconstruct_vk_url(data.vk_id)

    if not data.use_callback_message_as_status:
        status_message = await callback.message.answer("Cкачиваю " + url)
    else:
        status_message = callback.message
        if isinstance(status_message, Message):
            await status_message.edit_text("Cкачиваю " + url)

    if _is_button_callback(callback, VKDownloadButtonData.audio):
        async with YtdlpDownloader.download_audio(url) as audio:
            await callback.message.answer_audio(
                audio=audio.input_file,
                title=audio.title,
                performer="GKBOT",
                duration=audio.duration,
            )

    if _is_button_callback(callback, VKDownloadButtonData.video):
        async with YtdlpDownloader.download_video(url) as video:
            await send_video(
                callback.message.answer_video,
                video.input_file,
                metadata=video,
                height=video.height,
                width=video.width,
                duration=video.duration,
                supports_streaming=True,
            )

    if isinstance(status_message, Message):
        await status_message.delete()


def setup(r: Router):
    r.callback_query.register(download, F.data.startswith(PREFIX))
