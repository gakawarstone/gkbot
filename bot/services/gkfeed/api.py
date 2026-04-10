import json
from typing import AsyncGenerator

import aiohttp
from bs4 import BeautifulSoup

from ._types import FeedItem, GkfeedCredentials


class GkfeedApi:
    _api_root = "https://feed.gws.freemyip.com/api/v1/"

    def __init__(self, credentials: GkfeedCredentials) -> None:
        self.__login = credentials.login
        self.__password = credentials.password

    async def get_all_user_items(self) -> AsyncGenerator[FeedItem, None]:
        resp = await self._get_html(self._api_root + "get_items")
        data = json.loads(resp)

        for raw_item in data["items"]:
            if not raw_item["link"]:
                print(raw_item)
                continue

            item = self._convert_raw_data_to_feed_item(raw_item)
            yield item

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
