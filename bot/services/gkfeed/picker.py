from collections.abc import Callable
from typing import ClassVar

from ._types import FeedItem, FeedItemSummary
from .api import GkfeedApi
from .auth import GkfeedCredentials


class GkfeedItemsPicker:
    _items_pocket: ClassVar[dict[str, set[int]]] = {}

    def __init__(self, credentials: GkfeedCredentials) -> None:
        self.__credentials = credentials
        self._items_pocket.setdefault(credentials.login, set())

    async def get_next_item(
        self, is_item_valid: Callable[[FeedItemSummary], bool] = lambda _: True
    ) -> FeedItem | None:
        api = GkfeedApi(self.__credentials)
        items = [item async for item in api.get_user_items()]

        for summary in self._sort_items_by_feed(items):
            if not is_item_valid(summary) or self._is_item_in_pocket(summary.id):
                continue

            item = await api.get_item_by_item_id(summary.id)
            # Another picker may have delivered this ID while detail loaded.
            if item is None or self._is_item_in_pocket(item.id):
                continue

            self._save_to_pocket(item.id)
            return item

        self._clean_pocket()
        return None

    def _is_item_in_pocket(self, item_id: int) -> bool:
        return item_id in self._items_pocket[self.__credentials.login]

    def _save_to_pocket(self, item_id: int) -> None:
        self._items_pocket[self.__credentials.login].add(item_id)

    def _clean_pocket(self) -> None:
        self._items_pocket[self.__credentials.login] = set()

    def _sort_items_by_feed(
        self, items: list[FeedItemSummary]
    ) -> list[FeedItemSummary]:
        items_by_id = sorted(items, key=lambda x: x.id)

        items_by_feed: dict[int, list[FeedItemSummary]] = {}
        for item in items_by_id:
            feed_id = item.feed_id
            if feed_id not in items_by_feed:
                items_by_feed[feed_id] = []
            items_by_feed[feed_id].append(item)

        final_sorted_items = []
        processed_feed_ids = set()

        for item in items_by_id:
            feed_id = item.feed_id
            if feed_id in processed_feed_ids:
                continue

            final_sorted_items.extend(items_by_feed[feed_id])
            processed_feed_ids.add(feed_id)

        return final_sorted_items
