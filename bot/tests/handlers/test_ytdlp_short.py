from typing import override

import pytest

from handlers.text.ytdlp_short import YtdlpShortVideoHandler
from .. import integration_test
from . import Event, Bot


class MockedHandler(YtdlpShortVideoHandler):
    @property  # type: ignore[override]
    @override
    def bot(self) -> Bot:  # type: ignore[override]
        return Bot()


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_handler():
    await MockedHandler(  # type: ignore[call-arg]
        event=Event(
            text="https://x.com/i/status/1919231128180810005",
            breakpoint_at_delete=False,
        )  # type: ignore[arg-type]
    ).handle()