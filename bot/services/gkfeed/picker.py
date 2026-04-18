from typing import Callable

from ._types import FeedItem
from .api import GkfeedApi
from .auth import GkfeedCredentials


class GkfeedItemsPicker:
    _items_pocket: dict[str, list[int]] = {}

    def __init__(self, credentials: GkfeedCredentials):
        self.__credentials = credentials

    async def get_next_item(
        self, is_item_valid: Callable[[FeedItem], bool] = lambda _: True
    ) -> FeedItem | None:
        item = None
        api = GkfeedApi(self.__credentials)

        async for _item in api.get_all_user_items():
            if not is_item_valid(_item):
                continue

            if not self._is_item_in_pocket(_item.id):
                item = _item
                self._save_to_pocket(item.id)
                break

        if not item:
            self._clean_pocket()

        return item

    def _is_item_in_pocket(self, item_id: int) -> bool:
        if self.__credentials.login not in self._items_pocket:
            self._items_pocket[self.__credentials.login] = []

        return item_id in self._items_pocket[self.__credentials.login]

    def _save_to_pocket(self, item_id: int) -> None:
        if self.__credentials.login not in self._items_pocket:
            self._items_pocket[self.__credentials.login] = []

        self._items_pocket[self.__credentials.login].append(item_id)

    def _clean_pocket(self) -> None:
        self._items_pocket[self.__credentials.login] = []

    def _sort_items_by_feed(self, items: list[dict]) -> list[dict]:
        items_by_id = sorted(items, key=lambda x: x["id"])

        items_by_feed: dict[int, list[dict]] = {}
        for item in items_by_id:
            feed_id = item["feed_id"]
            if feed_id not in items_by_feed:
                items_by_feed[feed_id] = []
            items_by_feed[feed_id].append(item)

        final_sorted_items = []
        processed_feed_ids = set()

        for item in items_by_id:
            feed_id = item["feed_id"]
            if feed_id in processed_feed_ids:
                continue

            final_sorted_items.extend(items_by_feed[feed_id])
            processed_feed_ids.add(feed_id)

        return final_sorted_items
