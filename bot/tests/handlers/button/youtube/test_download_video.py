import pytest

from ui.buttons.youtube.download import (
    YoutubeDownloadButtonCallbackDataSerializer,
    YoutubeDownloadButtonData,
    YoutubeDownloadButtonCallbackData,
)
from handlers.button.youtube.download import download

# FIX: move to tests._utils or mocks
from tests.handlers import CallbackEvent, INTEGRATION_TEST


@pytest.mark.skipif(
    not INTEGRATION_TEST,
    reason="It tests if yt_dlp can download video it cant be mocked",
)
@pytest.mark.asyncio(loop_scope="session")
async def test_download_video():
    yt_code = "oRxuDeZRFx8"
    # TODO: YoutubeDownloadVideoButton(type=type.Video | type.Audio)
    callback_data = YoutubeDownloadButtonCallbackDataSerializer.serialize(
        YoutubeDownloadButtonData.video,
        YoutubeDownloadButtonCallbackData(yt_code),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
