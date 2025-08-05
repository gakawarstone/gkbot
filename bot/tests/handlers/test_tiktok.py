from typing import override

import pytest

from handlers.text.tiktok import TikTokVideoHandler
from .. import integration_test
from . import Event, Bot


class MockedHandler(TikTokVideoHandler):
    @property  # type: ignore[override]
    @override
    def bot(self) -> Bot:  # type: ignore[override]
        return Bot()


async def _handle_url(url: str):
    await MockedHandler(event=Event(text=url, breakpoint_at_delete=False)).handle()  # type: ignore[arg-type]


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_download_video():
    await _handle_url("https://vm.tiktok.com/ZMBwPoDGc/")


@integration_test
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