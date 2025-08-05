from typing import AsyncGenerator, override

import pytest

from services.gkfeed import FeedItem
from modules.feed import ShowFeedItemsHandler
from .. import integration_test
from . import Bot, Event


class GkfeedService:
    async def get_all_user_items(self) -> AsyncGenerator[FeedItem, None]:
        links = [
            "https://trashbox.ru/link/2025-03-10-iphone-17-air-iphone-17-pro",
            "https://www.piokok.com/post/6733377018605557242512/",
            "https://www.youtube.com/watch?v=5WMmPoHbQOo",
            "https://ranobe.me/ranobe24/6117",
        ]

        for i, link in enumerate(links):
            yield FeedItem(id=i + 1, title=f"link {i + 1}", feed_id=1, link=link)


class MockedHandler(ShowFeedItemsHandler):
    _gkfeed = GkfeedService()

    @property  # type: ignore[override]
    @override
    def bot(self) -> Bot:  # type: ignore[override]
        return Bot()


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_handler():
    await MockedHandler(event=Event(breakpoint_at_delete=False)).handle()  # type: ignore[arg-type]

