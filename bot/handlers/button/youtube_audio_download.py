from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.ytdlp import YtdlpDownloader
from ui.buttons.youtube import (
    YoutubeDownloadAudioButtonData,
    YoutubeDownloadAudioButtonDataSerializer,
)


async def download_audio(callback: CallbackQuery):
    video_code = callback.data.split(":")[-1]
    url = "https://www.youtube.com/watch?v=" + video_code
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
