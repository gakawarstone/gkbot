import json
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator

import aiohttp
from bs4 import BeautifulSoup

from ._types import FeedItem, GkfeedCredentials

logger = logging.getLogger(__name__)


class GkfeedRequestError(Exception):
    "Gkfeed request error"


class GkfeedApi:
    _api_root = "https://feed.gws.freemyip.com/api/v1/"
    _request_attempts = 3
    _cache_ttl = timedelta(minutes=1)

    def __init__(self, credentials: GkfeedCredentials) -> None:
        self.__login = credentials.login
        self.__password = credentials.password
        self.__response_cache: dict[str, tuple[float, bytes]] = {}

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
        self._clear_cache()

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
        self._clear_cache()

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

    async def _get_html(self, url: str) -> bytes:
        cached_response = self._get_cached_response(url)
        if cached_response is not None:
            return cached_response

        auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)

        for attempt in range(1, self._request_attempts + 1):
            try:
                async with aiohttp.ClientSession(conn_timeout=None) as session:
                    async with session.get(url, auth=auth) as response:
                        response.raise_for_status()
                        payload = await response.read()
                        self._set_cached_response(url, payload)
                        return payload
            except aiohttp.ClientError as exc:
                if attempt == self._request_attempts:
                    raise GkfeedRequestError from exc

                logger.warning(
                    "Gkfeed request failed on attempt %s/%s for %s: %s",
                    attempt,
                    self._request_attempts,
                    url,
                    exc,
                )

        raise GkfeedRequestError

    def _get_cached_response(self, url: str) -> bytes | None:
        cached_response = self.__response_cache.get(url)
        if cached_response is None:
            return None

        expires_at, payload = cached_response
        if self._get_current_timestamp() > expires_at:
            self.__response_cache.pop(url, None)
            return None

        return payload

    def _set_cached_response(self, url: str, payload: bytes) -> None:
        expires_at = self._get_current_timestamp() + self._cache_ttl.total_seconds()
        self.__response_cache[url] = (expires_at, payload)

    def _clear_cache(self) -> None:
        self.__response_cache.clear()

    @staticmethod
    def _get_current_timestamp() -> float:
        return datetime.now().timestamp()
