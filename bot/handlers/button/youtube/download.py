from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.ytdlp import YtdlpDownloader
from ui.buttons.youtube.download import (
    YoutubeDownloadButtonData,
    YoutubeDownloadButtonDataSerializer,
    YoutubeDownloadButtonCallbackDataDeserializer,
    PREFIX,
)


def _get_video_url(callback: CallbackQuery) -> str:
    if callback.data is None:
        raise ValueError("Callback data cannot be None")

    deserializer = YoutubeDownloadButtonCallbackDataDeserializer()
    data = deserializer.deserialize(callback.data)
    return "https://www.youtube.com/watch?v=" + data.yt_video_code


def _is_button_callback(
    callback: CallbackQuery, button_data: YoutubeDownloadButtonData
) -> bool:
    if callback.data is None:
        return False

    return callback.data.startswith(
        YoutubeDownloadButtonDataSerializer.get_full_prefix(button_data)
    )


async def download(callback: CallbackQuery):
    if callback.message is None:
        return

    url = _get_video_url(callback)
    status_message = await callback.message.answer("Cкачиваю " + url)

    if _is_button_callback(callback, YoutubeDownloadButtonData.audio):
        audio = await YtdlpDownloader.download_audio(url)
        await callback.message.answer_audio(
            audio=audio.input_file,
            title=audio.title,
            performer="GKBOT",
            duration=audio.duration,
        )

    if _is_button_callback(callback, YoutubeDownloadButtonData.video):
        video = await YtdlpDownloader.download_video(url)
        await callback.message.answer_video(
            video.input_file,
            height=video.height,
            width=video.width,
            duration=video.duration,
            supports_streaming=True,
        )

    await status_message.delete()


def setup(r: Router):
    r.callback_query.register(download, F.data.startswith(PREFIX))
