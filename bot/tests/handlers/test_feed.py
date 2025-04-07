from typing import AsyncGenerator, override

import pytest

from services.gkfeed import FeedItem
from handlers.user.feed import ShowFeedItemsHandler
from . import Bot, Event, integration_test


class GkfeedService:
    async def get_all_user_items(self) -> AsyncGenerator[FeedItem, None]:
        items = [
            # FeedItem(
            #     id=1,
            #     feed_id=1,
            #     link="https://trashbox.ru/link/2025-03-10-iphone-17-air-iphone-17-pro",
            # ),
            # FeedItem(
            #     id=1,
            #     feed_id=1,
            #     link="https://www.piokok.com/post/6745656138125062123563/",
            # ),
            FeedItem(
                id=1,
                feed_id=1,
                link="https://www.youtube.com/watch?v=5WMmPoHbQOo",
            ),
        ]

        for item in items:
            yield item


class MockedHandler(ShowFeedItemsHandler):
    _gkfeed = GkfeedService()

    @property
    @override
    def bot(self) -> Bot:
        return Bot()


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_handler():
    await MockedHandler(event=Event(breakpoint_at_delete=False)).handle()
