from typing import override

import pytest

from handlers.text.tiktok import TikTokVideoHandler
from tests import integration_test
from . import Event, Bot


class MockedHandler(TikTokVideoHandler):
    @property
    @override
    def bot(self) -> Bot:
        return Bot()


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_download_video():
    await MockedHandler(
        event=Event(text="https://vm.tiktok.com/ZMBwPoDGc/", breakpoint_at_delete=False)
    ).handle()


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_download_slideshow():
    await MockedHandler(
        event=Event(text="https://vt.tiktok.com/ZShECspQn/", breakpoint_at_delete=False)
    ).handle()
    await MockedHandler(
        event=Event(text="https://vt.tiktok.com/ZSk1SHU9U/", breakpoint_at_delete=False)
    ).handle()
