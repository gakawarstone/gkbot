import asyncio
import json
from collections.abc import AsyncGenerator
from time import monotonic
from typing import ClassVar

import aiohttp
from bs4 import BeautifulSoup

from ._decoder import FeedDecoder
from ._types import FeedItem, FeedItemSummary, GkfeedCredentials


class GkfeedApi:
    _api_root = "https://feed.gws.freemyip.com/api/v1/"
    _items_lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _items_decoder: ClassVar[FeedDecoder] = FeedDecoder()
    _items_cache: ClassVar[
        dict[tuple[str, str, int, int | None], tuple[float, list[FeedItemSummary]]]
    ] = {}

    def __init__(self, credentials: GkfeedCredentials) -> None:
        self.__login = credentials.login
        self.__password = credentials.password

    async def get_user_items(
        self, limit: int = 1000, cursor: int | None = None
    ) -> AsyncGenerator[FeedItemSummary]:
        cache_key = (self.__login, self.__password, limit, cursor)
        async with self._items_lock:
            now = monotonic()
            expired_keys = [
                key
                for key, (expires_at, _) in self._items_cache.items()
                if expires_at <= now
            ]
            for key in expired_keys:
                del self._items_cache[key]

            cached = self._items_cache.get(cache_key)
            if cached is None:
                url = self._api_root + f"get_items?view=summary&limit={limit}"
                if cursor:
                    url += f"&cursor={cursor}"
                items = await self._items_decoder.decode(await self._get_html(url))
                self._items_cache[cache_key] = (monotonic() + 300, items)
            else:
                items = cached[1]

        for item in items:
            yield item

    @classmethod
    async def on_startup(cls) -> None:
        await cls._items_decoder.start()

    @classmethod
    async def on_shutdown(cls) -> None:
        await cls._items_decoder.close()

    async def delete_item_by_id(self, item_id: int) -> None:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)
            async with session.delete(
                self._api_root + f"items/{item_id}", auth=auth
            ) as response:
                await response.read()

    async def add_feed_lazy(self, feed_url: str) -> None:
        url = self._api_root + "add_lazy"
        body = {"url": feed_url}
        json_data = json.dumps(body)
        auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)
        async with (
            aiohttp.ClientSession(conn_timeout=None) as session,
            session.post(url, auth=auth, data=json_data) as response,
        ):
            resp = await response.content.read()
        resp = json.loads(resp)
        if not resp["created"]:
            raise ValueError

    async def get_item_by_item_id(self, item_id: int) -> FeedItem | None:
        try:
            resp = await self._get_html(self._api_root + f"item?id={item_id}")
        except aiohttp.ClientResponseError as error:
            if error.status == 404:
                return None
            raise
        data = json.loads(resp)
        item = data["item"]
        return FeedItem(
            id=item["id"],
            feed_id=item["feed_id"],
            link=item["link"],
            title=item["title"],
            text=item["text"],
        )

    async def get_raw_item_data(self, item_id: int) -> dict:
        resp = await self._get_html(self._api_root + f"item?id={item_id}")
        return json.loads(resp)

    async def _get_soup(self, url: str) -> BeautifulSoup:
        html = await self._get_html(url)
        return BeautifulSoup(html, "xml")

    async def _get_html(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)
            async with session.get(url, auth=auth) as response:
                response.raise_for_status()
                return await response.read()
