from typing import override

import pytest

from handlers.text.ytdlp_short import YtdlpShortVideoHandler
from .. import integration_test
from ..mocks.db import use_db
from . import Event, Bot


class MockedHandler(YtdlpShortVideoHandler):
    @property  # type: ignore[override]
    @override
    def bot(self) -> Bot:  # type: ignore[override]
        return Bot()


async def _handle_url(url: str):
    await MockedHandler(event=Event(text=url, breakpoint_at_delete=False)).handle()  # type: ignore[arg-type]


@integration_test
@use_db
@pytest.mark.asyncio(loop_scope="session")
async def test_download_reel():
    await _handle_url(
        "https://www.instagram.com/reel/DPbFv6TDG1R/?igsh=MTZtYXQzYTc1b2R1MA=="
    )
