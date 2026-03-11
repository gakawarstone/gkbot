import pytest

from handlers.button.vk.download import download
from ui.buttons.vk import (
    VKDownloadButtonCallbackDataSerializer,
    VKDownloadButtonData,
    VKDownloadButtonCallbackData,
)
from utils.vk import get_vk_id

from .... import integration_test
from ....mocks.db import use_db
from tests.handlers import CallbackEvent


@integration_test
@use_db
@pytest.mark.asyncio(loop_scope="session")
async def test_download_video():
    url = "https://vk.com/video-50883936_456244451"
    vk_id = get_vk_id(url)
    callback_data = VKDownloadButtonCallbackDataSerializer.serialize(
        VKDownloadButtonData.video,
        VKDownloadButtonCallbackData(vk_id=vk_id),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
