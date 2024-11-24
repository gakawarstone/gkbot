import json
import random
from typing import AsyncGenerator
from dataclasses import dataclass

import aiohttp
from bs4 import BeautifulSoup


@dataclass
class FeedItem:
    id: int
    feed_id: int
    link: str


class GkfeedService:
    _api_root = "http://feed.gws.freemyip.com/api/v1/"

    def __init__(self, login: str, password: str) -> None:
        self.__login = login
        self.__password = password

    async def get_all_user_items(self) -> AsyncGenerator[FeedItem, None]:
        resp = await self._get_html(self._api_root + "get_items")
        data = json.loads(resp)

        sorted_items = sorted(data["items"], key=lambda x: x["id"], reverse=True)

        if sorted_items and sorted_items[0]["link"]:
            first_item = sorted_items[0]
            yield FeedItem(
                id=first_item["id"],
                feed_id=first_item["feed_id"],
                link=first_item["link"],
            )

        remaining_items = sorted_items[1:]
        random.shuffle(remaining_items)
        for i in remaining_items:
            if not i["link"]:
                continue
            yield FeedItem(id=i["id"], feed_id=i["feed_id"], link=i["link"])

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

    async def _get_soup(self, url: str) -> BeautifulSoup:
        html = await self._get_html(url)
        return BeautifulSoup(html, "xml")

    async def _get_html(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)
            async with session.get(url, auth=auth) as response:
                return await response.read()
