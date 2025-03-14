from handlers.button.youtube.download_audio import download_audio
from ui.buttons.youtube.download_audio import (
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
