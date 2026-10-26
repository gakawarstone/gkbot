import pytest

from handlers.button.vk.download import download
from tests.handlers import CallbackEvent
from ui.buttons.vk import (
    VKDownloadButtonCallbackData,
    VKDownloadButtonCallbackDataSerializer,
    VKDownloadButtonData,
)
from utils.vk import get_vk_id

from .... import integration_test


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_download_audio():
    url = "https://vk.com/video-50883936_456244451"
    vk_id = get_vk_id(url)
    callback_data = VKDownloadButtonCallbackDataSerializer.serialize(
        VKDownloadButtonData.audio,
        VKDownloadButtonCallbackData(vk_id=vk_id),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
