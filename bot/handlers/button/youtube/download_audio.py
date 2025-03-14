from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.ytdlp import YtdlpDownloader
from ui.buttons.youtube.download_audio import (
    YoutubeDownloadAudioButtonData,
    YoutubeDownloadAudioButtonDataSerializer,
    YoutubeDownloadAudioButtonCallbackDataDeserializer,
)


async def download_audio(callback: CallbackQuery):
    deserializer = YoutubeDownloadAudioButtonCallbackDataDeserializer()
    data = deserializer.deserialize(callback.data)
    url = "https://www.youtube.com/watch?v=" + data.yt_video_code

    status_message = await callback.message.answer("Cкачиваю " + url)
    audio = await YtdlpDownloader.download_audio(url)

    await callback.message.answer_audio(
        audio=audio.input_file,
        title=audio.title,
        performer="GKBOT",
        duration=audio.duration,
    )

    await status_message.delete()


def setup(r: Router):
    r.callback_query.register(
        download_audio,
        F.data.startswith(
            YoutubeDownloadAudioButtonDataSerializer.get_full_prefix(
                YoutubeDownloadAudioButtonData()
            )
        ),
    )
