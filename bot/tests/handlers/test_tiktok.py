from typing import override

import pytest

from handlers.text.tiktok import TikTokVideoHandler

from .. import requires_integration
from . import Bot, Event


class MockedHandler(TikTokVideoHandler):
    @property  # type: ignore[override]
    @override
    def bot(self) -> Bot:  # type: ignore[override]
        return Bot()


async def _handle_url(url: str):
    await MockedHandler(event=Event(text=url)).handle()  # type: ignore[arg-type]


@requires_integration(
    "Telegram Bot API credentials, ADMIN_IDS and live TikTok providers, yt-dlp and ffmpeg"
)
@pytest.mark.asyncio(loop_scope="session")
async def test_download_video():
    await _handle_url("https://vm.tiktok.com/ZGdm6LB6D/")


@requires_integration(
    "Telegram Bot API credentials, ADMIN_IDS and live TikTok providers, yt-dlp and ffmpeg"
)
@pytest.mark.asyncio(loop_scope="session")
async def test_download_slideshow():
    urls = [
        # "https://vt.tiktok.com/ZShECspQn/",
        # "https://vt.tiktok.com/ZSk1SHU9U/",
        # "https://vt.tiktok.com/ZSkhnmgaB/",
        "https://vt.tiktok.com/ZSkMFNRau/",
    ]
    for url in urls:
        await _handle_url(url)
