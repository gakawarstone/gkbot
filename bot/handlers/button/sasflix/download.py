from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage, URLInputFile

from services.sasflix import SasflixService
from ui.buttons.sasflix import (
    PREFIX,
    SasflixDownloadButtonCallbackDataDeserializer,
)


async def download(callback: CallbackQuery) -> None:
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        raise ValueError("Callback message is inaccessible or None")
    if callback.data is None:
        raise ValueError("Callback data cannot be None")

    callback_data = SasflixDownloadButtonCallbackDataDeserializer.deserialize(
        callback.data
    )
    topic_url = f"https://sasflix.ru/topics/{callback_data.topic_uuid}"
    status_message = await callback.message.answer("Cкачиваю " + topic_url)

    audio = await SasflixService.get_audio(topic_url)
    await callback.message.answer_audio(
        audio=URLInputFile(SasflixService.get_audio_url(audio.uuid)),
        title=audio.title,
        performer="GKBOT",
        duration=audio.duration,
    )

    await status_message.delete()


def setup(router: Router) -> None:
    router.callback_query.register(download, F.data.startswith(PREFIX))
