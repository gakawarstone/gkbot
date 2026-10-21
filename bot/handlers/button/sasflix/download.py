from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage, URLInputFile
from configs.timeouts import AUDIO_TRANSFER_TIMEOUT_SECONDS
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
    if callback.bot is None:
        raise ValueError("Callback bot is not configured")

    callback_data = SasflixDownloadButtonCallbackDataDeserializer.deserialize(
        callback.data
    )
    topic_url = f"https://sasflix.ru/topics/{callback_data.topic_uuid}"
    status_message = await callback.message.answer("Cкачиваю " + topic_url)

    audio = await SasflixService.get_audio(topic_url)
    await callback.bot(
        callback.message.answer_audio(
            audio=URLInputFile(
                SasflixService.get_audio_url(audio.uuid),
                timeout=AUDIO_TRANSFER_TIMEOUT_SECONDS,
            ),
            title=audio.title,
            performer="GKBOT",
            duration=audio.duration,
        ),
        request_timeout=AUDIO_TRANSFER_TIMEOUT_SECONDS,
    )

    await status_message.delete()


def setup(router: Router) -> None:
    router.callback_query.register(download, F.data.startswith(PREFIX))
