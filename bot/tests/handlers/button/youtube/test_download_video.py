import pytest

from handlers.button.youtube.download import download
from tests.handlers import CallbackEvent
from ui.buttons.youtube.download import (
    YoutubeDownloadButtonCallbackData,
    YoutubeDownloadButtonCallbackDataSerializer,
    YoutubeDownloadButtonData,
)

from .... import integration_test


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_download_video():
    yt_code = "oRxuDeZRFx8"
    callback_data = YoutubeDownloadButtonCallbackDataSerializer.serialize(
        YoutubeDownloadButtonData.video,
        YoutubeDownloadButtonCallbackData(yt_code),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
