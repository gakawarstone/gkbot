import json
from typing import AsyncGenerator
from dataclasses import dataclass

import aiohttp
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class FeedItem:
    id: int
    feed_id: int
    link: str
    title: str
    text: str


class GkfeedService:
    _api_root = "https://feed.gws.freemyip.com/api/v1/"
    _items_pocket: dict[str, list[int]] = {}

    def __init__(self, login: str, password: str) -> None:
        self.__login = login
        self.__password = password

    async def get_all_user_items(self) -> AsyncGenerator[FeedItem, None]:
        if self.__login not in self._items_pocket:
            self._items_pocket[self.__login] = []

        resp = await self._get_html(self._api_root + "get_items")
        data = json.loads(resp)
        items = self._sort_items_by_feed(data["items"])

        for raw_item in items:
            if not raw_item["link"]:
                print(raw_item)
                continue

            item = self._convert_raw_data_to_feed_item(raw_item)
            if self._should_return_item_using_pocket_strategy(item):
                yield item

        self._items_pocket[self.__login] = []

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

    def _should_return_item_using_pocket_strategy(self, item: FeedItem) -> bool:
        if item.id not in self._items_pocket[self.__login]:
            self._items_pocket[self.__login].append(item.id)
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

    async def add_feed_lazy(self, feed_url: str) -> None:
        url = self._api_root + "add_lazy"
        body = {"url": feed_url}
        json_data = json.dumps(body)
        auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)
        async with aiohttp.ClientSession(conn_timeout=None) as session:
            async with session.post(url, auth=auth, data=json_data) as response:
                resp = await response.content.read()
        resp = json.loads(resp)
        if not resp["created"]:
            raise ValueError

    async def get_items_from_feed(self, feed_id: int) -> AsyncGenerator[FeedItem, None]:
        async for item in self.get_all_user_items():
            if item.feed_id == feed_id:
                yield item

    async def get_item_by_item_id(self, item_id: int) -> FeedItem:
        resp = await self._get_html(self._api_root + f"item?id={item_id}")
        data = json.loads(resp)
        item = data["item"]
        return self._convert_raw_data_to_feed_item(item)

    async def get_raw_item_data(self, item_id: int) -> dict:
        resp = await self._get_html(self._api_root + f"item?id={item_id}")
        return json.loads(resp)

    @staticmethod
    def _convert_raw_data_to_feed_item(raw_data: dict) -> FeedItem:
        return FeedItem(
            id=raw_data["id"],
            feed_id=raw_data["feed_id"],
            link=raw_data["link"],
            title=raw_data["title"],
            text=raw_data["text"],
        )

    async def _get_soup(self, url: str) -> BeautifulSoup:
        html = await self._get_html(url)
        return BeautifulSoup(html, "xml")

    async def _get_html(self, url: str, body={}) -> bytes:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)
            async with session.get(url, auth=auth) as response:
                return await response.read()
