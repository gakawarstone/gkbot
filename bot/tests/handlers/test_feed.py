from collections.abc import Callable
from typing import ClassVar, override
from unittest.mock import patch

import pytest

from modules.feed import ShowFeedItemsHandler
from services.gkfeed import (
    FeedItem,
    GkfeedCredentials,
    GkfeedItemsPicker,
)

from .. import requires_integration
from . import Bot, Event


class MockedGkfeedItemsPicker(GkfeedItemsPicker):
    # TODO: use Event(text=link) and get_next_item this link
    LINKS: ClassVar[list[str]] = [
        "https://trashbox.ru/link/2025-03-10-iphone-17-air-iphone-17-pro",
        "https://www.youtube.com/watch?v=5WMmPoHbQOo",
        "https://ranobe.me/ranobe24/6117",
    ]

    def __init__(self, credentials: GkfeedCredentials) -> None:
        super().__init__(credentials)
        self._index = 0

    @override
    async def get_next_item(
        self, is_item_valid: Callable[[FeedItem], bool] = lambda _: True
    ) -> FeedItem | None:  # type: ignore[override]
        while self._index < len(self.LINKS):
            i = self._index
            self._index += 1
            item = FeedItem(
                id=i + 1,
                title=f"link {i + 1}",
                feed_id=1,
                link=self.LINKS[i],
                text="",
            )
            if is_item_valid(item):
                return item

        return None


class MockedHandler(ShowFeedItemsHandler):
    _items_limit = 1

    @property
    async def _gkfeed_credentials(self) -> GkfeedCredentials:  # type: ignore[override]
        return GkfeedCredentials(login="test", password="test")

    @property  # type: ignore[override]
    @override
    def bot(self) -> Bot:  # type: ignore[override]
        return Bot()


@requires_integration(
    "Telegram Bot API credentials, ADMIN_IDS and live article/YouTube endpoints and the yt-dlp worker"
)
@pytest.mark.asyncio(loop_scope="session")
async def test_handler():
    with (
        patch(
            "modules.feed.handlers.messages.GkfeedItemsPicker", MockedGkfeedItemsPicker
        ),
        patch("modules.feed.handlers.messages.Message", Event),
    ):
        for _ in range(3):
            await MockedHandler(event=Event()).handle()  # type: ignore[arg-type]
