import pytest

from handlers.button.youtube.download import download
from ui.buttons.youtube.download import (
    YoutubeDownloadButtonCallbackDataSerializer,
    YoutubeDownloadButtonData,
    YoutubeDownloadButtonCallbackData,
)

# FIX: move to tests._utils or mocks
from tests.handlers import CallbackEvent, INTEGRATION_TEST


@pytest.mark.skipif(
    not INTEGRATION_TEST,
    reason="It tests if yt_dlp can download audio it cant be mocked",
)
@pytest.mark.asyncio(loop_scope="session")
async def test_download_audio():
    yt_code = "oRxuDeZRFx8"
    callback_data = YoutubeDownloadButtonCallbackDataSerializer.serialize(
        YoutubeDownloadButtonData.audio,
        YoutubeDownloadButtonCallbackData(yt_code),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
