import pytest

from ui.buttons.youtube.download import (
    YoutubeDownloadButtonCallbackDataSerializer,
    YoutubeDownloadButtonData,
    YoutubeDownloadButtonCallbackData,
)
from handlers.button.youtube.download import download

# FIX: move to tests._utils or mocks
from tests.handlers import CallbackEvent, integration_test


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_download_video():
    yt_code = "oRxuDeZRFx8"
    # TODO: YoutubeDownloadVideoButton(type=type.Video | type.Audio)
    callback_data = YoutubeDownloadButtonCallbackDataSerializer.serialize(
        YoutubeDownloadButtonData.video,
        YoutubeDownloadButtonCallbackData(yt_code),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
