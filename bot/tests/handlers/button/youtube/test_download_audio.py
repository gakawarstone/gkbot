import pytest

from handlers.button.youtube.download import download
from tests.handlers import CallbackEvent
from ui.buttons.youtube.download import (
    YoutubeDownloadButtonCallbackData,
    YoutubeDownloadButtonCallbackDataSerializer,
    YoutubeDownloadButtonData,
)

from .... import requires_integration


@requires_integration(
    "Telegram Bot API credentials, ADMIN_IDS and YouTube network access and the yt-dlp worker"
)
@pytest.mark.asyncio(loop_scope="session")
async def test_download_audio():
    yt_code = "oRxuDeZRFx8"
    callback_data = YoutubeDownloadButtonCallbackDataSerializer.serialize(
        YoutubeDownloadButtonData.audio,
        YoutubeDownloadButtonCallbackData(yt_code),
    )
    await download(CallbackEvent(callback_data))  # type:ignore
