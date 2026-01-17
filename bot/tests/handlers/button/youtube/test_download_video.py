import pytest

from ui.buttons.youtube.download import (
    YoutubeDownloadButtonCallbackDataSerializer,
    YoutubeDownloadButtonData,
    YoutubeDownloadButtonCallbackData,
)
from handlers.button.youtube.download import download

from .... import integration_test
from ....mocks.db import use_db
from tests.handlers import CallbackEvent


@integration_test
@use_db
@pytest.mark.asyncio(loop_scope="session")
async def test_download_video():
    yt_code = "oRxuDeZRFx8"
    callback_data = YoutubeDownloadButtonCallbackDataSerializer.serialize(
        YoutubeDownloadButtonData.video,
        YoutubeDownloadButtonCallbackData(yt_code),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
