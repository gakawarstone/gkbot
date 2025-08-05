import pytest

from handlers.button.youtube.download import download
from ui.buttons.youtube.download import (
    YoutubeDownloadButtonCallbackDataSerializer,
    YoutubeDownloadButtonData,
    YoutubeDownloadButtonCallbackData,
)

from .... import integration_test
from tests.handlers import CallbackEvent


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_download_audio():
    yt_code = "oRxuDeZRFx8"
    callback_data = YoutubeDownloadButtonCallbackDataSerializer.serialize(
        YoutubeDownloadButtonData.audio,
        YoutubeDownloadButtonCallbackData(yt_code),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
