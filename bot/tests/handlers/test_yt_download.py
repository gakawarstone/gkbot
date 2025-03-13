from handlers.buttons.youtube_audio_download import download_audio
from ui.buttons.youtube import (
    YoutubeDownloadAudioButtonCallbackDataSerializer,
    YoutubeDownloadAudioButtonData,
    YoutubeDownloadAudioButtonCallbackData,
)
from . import CallbackEvent


async def test_download_audio():
    yt_code = "cfoJV07tibg"
    callback_data = YoutubeDownloadAudioButtonCallbackDataSerializer.serialize(
        YoutubeDownloadAudioButtonData(),
        YoutubeDownloadAudioButtonCallbackData(yt_code),
    )
    await download_audio(CallbackEvent(callback_data))  # type:ignore
