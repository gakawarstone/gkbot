from typing import override

import pytest

from handlers.text.ytdlp_short import YtdlpShortVideoHandler
from .. import requires_integration
from . import Event, Bot


class MockedHandler(YtdlpShortVideoHandler):
    @property  # type: ignore[override]
    @override
    def bot(self) -> Bot:  # type: ignore[override]
        return Bot()


@requires_integration(
    "Telegram Bot API credentials, ADMIN_IDS and X network access, yt-dlp and ffmpeg"
)
@pytest.mark.asyncio(loop_scope="session")
async def test_handler_x_short_link():
    await MockedHandler(  # type: ignore[call-arg]
        event=Event(
            text="https://x.com/i/status/1919231128180810005",
        )  # type: ignore[arg-type]
    ).handle()


@requires_integration(
    "Telegram Bot API credentials, ADMIN_IDS and X network access, yt-dlp and ffmpeg"
)
@pytest.mark.asyncio(loop_scope="session")
async def test_handler_x_long_list():
    await MockedHandler(  # type: ignore[call-arg]
        event=Event(
            text="https://x.com/thestanduppod/status/2028833375046238538?s=46",
        )  # type: ignore[arg-type]
    ).handle()
