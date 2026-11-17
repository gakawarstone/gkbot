from collections.abc import Callable
from typing import override
from unittest.mock import patch

import pytest

from modules.feed import ShowFeedItemsHandler
from services.gkfeed import (
    FeedItem,
    FeedItemSummary,
    GkfeedCredentials,
    GkfeedItemsPicker,
)

from .. import requires_integration
from . import Bot, Event


class MockedGkfeedItemsPicker(GkfeedItemsPicker):
    def __init__(self, credentials: GkfeedCredentials, link: str) -> None:
        super().__init__(credentials)
        self._link = link
        self._returned = False

    @override
    async def get_next_item(
        self, is_item_valid: Callable[[FeedItemSummary], bool] = lambda _: True
    ) -> FeedItem | None:  # type: ignore[override]
        if not self._returned:
            self._returned = True
            item = FeedItem(
                id=1,
                title="link 1",
                feed_id=1,
                link=self._link,
                text="",
            )
            if is_item_valid(
                FeedItemSummary(item.id, item.feed_id, item.link, item.title, "")
            ):
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
@pytest.mark.parametrize(
    "link",
    [
        "https://trashbox.ru/link/2025-03-10-iphone-17-air-iphone-17-pro",
        "https://www.youtube.com/watch?v=5WMmPoHbQOo",
        "https://ranobe.me/ranobe24/6117",
    ],
)
async def test_handler(link: str) -> None:
    with (
        patch(
            "modules.feed.handlers.messages.GkfeedItemsPicker",
            side_effect=lambda credentials: MockedGkfeedItemsPicker(credentials, link),
        ),
        patch("modules.feed.handlers.messages.Message", Event),
    ):
        await MockedHandler(event=Event()).handle()  # type: ignore[arg-type]
