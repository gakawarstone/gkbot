from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.ytdlp import YtdlpDownloader
from ui.buttons.youtube.download_video import (
    YoutubeDownloadVideoButtonData,
    YoutubeDownloadVideoButtonDataSerializer,
    YoutubeDownloadVideoButtonCallbackDataDeserializer,
)


async def download_video(callback: CallbackQuery):
    deserializer = YoutubeDownloadVideoButtonCallbackDataDeserializer()
    data = deserializer.deserialize(callback.data)
    url = "https://www.youtube.com/watch?v=" + data.yt_video_code

    status_message = await callback.message.answer("Cкачиваю " + url)
    video_file = await YtdlpDownloader.download_video(url)

    await callback.message.answer_video(video_file, duration=180)

    await status_message.delete()


def setup(r: Router):
    r.callback_query.register(
        download_video,
        F.data.startswith(
            YoutubeDownloadVideoButtonDataSerializer.get_full_prefix(
                YoutubeDownloadVideoButtonData()
            )
        ),
    )
