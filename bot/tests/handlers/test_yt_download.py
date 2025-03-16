import pytest

from handlers.button.youtube.download_audio import download_audio
from ui.buttons.youtube.download_audio import (
    YoutubeDownloadAudioButtonCallbackDataSerializer,
    YoutubeDownloadAudioButtonData,
    YoutubeDownloadAudioButtonCallbackData,
)
from . import CallbackEvent, INTEGRATION_TEST


@pytest.mark.skipif(
    not INTEGRATION_TEST,
    reason="It tests if yt_dlp can download audio it cant be mocked",
)
@pytest.mark.asyncio(loop_scope="session")
async def test_download_audio():
    yt_code = "oRxuDeZRFx8"
    callback_data = YoutubeDownloadAudioButtonCallbackDataSerializer.serialize(
        YoutubeDownloadAudioButtonData(),
        YoutubeDownloadAudioButtonCallbackData(yt_code),
    )
    await download_audio(CallbackEvent(callback_data))  # type:ignore
