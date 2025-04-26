import json
from typing import AsyncGenerator
from dataclasses import dataclass

import aiohttp
from bs4 import BeautifulSoup


@dataclass
class FeedItem:
    id: int
    feed_id: int
    link: str
    title: str


class GkfeedService:
    _api_root = "https://feed.gws.freemyip.com/api/v1/"
    _items_priority: dict[int, int] = {}
    _items_offset: dict[int, int] = {}

    def __init__(self, login: str, password: str) -> None:
        self.__login = login
        self.__password = password

    async def get_all_user_items(self) -> AsyncGenerator[FeedItem, None]:
        resp = await self._get_html(self._api_root + "get_items")
        data = json.loads(resp)

        sorted_items = sorted(data["items"], key=lambda x: x["id"], reverse=True)

        for n, raw_item in enumerate(sorted_items):
            if not raw_item["link"]:
                print(raw_item)
                continue
            if n > 4:
                break
            item = self._convert_raw_data_to_feed_item(raw_item)
            if self._should_return_item_using_priority_strategy(item, n):
                yield item

        remaining_items = reversed(sorted_items)
        for n, raw_item in enumerate(remaining_items):
            if not raw_item["link"]:
                print(raw_item)
                continue

            item = self._convert_raw_data_to_feed_item(raw_item)
            if self._should_return_item_using_priority_strategy(item, n):
                yield item

    def _should_return_item_using_priority_strategy(
        self, item: FeedItem, current_item_nummer: int
    ) -> bool:
        if item.id not in self._items_priority:
            self._items_priority[item.id] = 0
        if item.id not in self._items_offset:
            self._items_offset[item.id] = 0

        self._items_offset[item.id] -= current_item_nummer + 1

        if self._items_offset[item.id] < 0:
            self._items_offset[item.id] = 0

        if self._items_offset[item.id] <= 0:
            self._items_priority[item.id] -= 5
            self._items_offset[item.id] -= self._items_priority[item.id]
            return True
        return False

    async def delete_item_by_id(self, item_id: int) -> None:
        headers = {"Content-Type": "application/json"}
        data = {"itemIds": [item_id]}
        json_data = json.dumps(data)
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)
            async with session.post(
                self._api_root + "add_deleted_items",
                data=json_data,
                auth=auth,
                headers=headers,
            ) as response:
                await response.read()

    async def get_items_from_feed(self, feed_id: int) -> AsyncGenerator[FeedItem, None]:
        async for item in self.get_all_user_items():
            if item.feed_id == feed_id:
                yield item

    async def get_item_by_item_id(self, item_id: int) -> FeedItem:
        resp = await self._get_html(self._api_root + f"item?id={item_id}")
        data = json.loads(resp)
        item = data["item"]
        return self._convert_raw_data_to_feed_item(item)

    @staticmethod
    def _convert_raw_data_to_feed_item(raw_data: dict) -> FeedItem:
        return FeedItem(
            id=raw_data["id"],
            feed_id=raw_data["feed_id"],
            link=raw_data["link"],
            title=raw_data["title"],
        )

    async def _get_soup(self, url: str) -> BeautifulSoup:
        html = await self._get_html(url)
        return BeautifulSoup(html, "xml")

    async def _get_html(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)
            async with session.get(url, auth=auth) as response:
                return await response.read()
