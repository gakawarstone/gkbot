from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage
from services.matreshka import MatreshkaService
from ui.buttons.matreshka import (
    PREFIX,
    MatreshkaDownloadButtonCallbackDataDeserializer,
)

_AUDIO_UPLOAD_TIMEOUT_SECONDS = 1800


async def download(callback: CallbackQuery) -> None:
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        raise ValueError("Callback message is inaccessible or None")
    if callback.data is None:
        raise ValueError("Callback data cannot be None")
    if callback.bot is None:
        raise ValueError("Callback bot is not configured")

    callback_data = MatreshkaDownloadButtonCallbackDataDeserializer.deserialize(
        callback.data
    )
    video_url = f"https://matreshka.tv/video/{callback_data.video_id}"
    status_message = await callback.message.answer("Cкачиваю " + video_url)

    video = await MatreshkaService.get_video(video_url)
    audio = await MatreshkaService.download_audio(video)
    await callback.bot(
        callback.message.answer_audio(
            audio=audio.input_file,
            title=audio.title,
            performer="GKBOT",
            duration=audio.duration,
        ),
        request_timeout=_AUDIO_UPLOAD_TIMEOUT_SECONDS,
    )

    await status_message.delete()


def setup(router: Router) -> None:
    router.callback_query.register(download, F.data.startswith(PREFIX))
