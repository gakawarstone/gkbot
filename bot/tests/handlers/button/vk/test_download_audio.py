import pytest

from handlers.button.vk.download import download
from ui.buttons.vk import (
    VKDownloadButtonCallbackDataSerializer,
    VKDownloadButtonData,
    VKDownloadButtonCallbackData,
)

from .... import integration_test
from tests.handlers import CallbackEvent


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_download_audio():
    url = "https://vk.com/video-50883936_456244451"
    callback_data = VKDownloadButtonCallbackDataSerializer.serialize(
        VKDownloadButtonData.audio,
        VKDownloadButtonCallbackData(url=url),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
