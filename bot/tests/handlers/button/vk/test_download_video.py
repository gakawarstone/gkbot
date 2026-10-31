import pytest

from handlers.button.vk.download import download
from tests.handlers import CallbackEvent
from ui.buttons.vk import (
    VKDownloadButtonCallbackData,
    VKDownloadButtonCallbackDataSerializer,
    VKDownloadButtonData,
)
from utils.vk import parse_vk_reference

from .... import integration_test


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_download_video() -> None:
    url = "https://vk.com/video-50883936_456244451"
    reference = parse_vk_reference(url)
    callback_data = VKDownloadButtonCallbackDataSerializer.serialize(
        VKDownloadButtonData.video,
        VKDownloadButtonCallbackData(reference=reference),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
