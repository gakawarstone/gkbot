import asyncio
import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import ClassVar
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup

from ._types import FeedItem, GkfeedCredentials


@dataclass
class _SyncState:
    items: dict[int, FeedItem] = field(default_factory=dict)
    cursor: str | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class GkfeedApi:
    _api_root = "https://feed.gws.freemyip.com/api/v1/"
    _api_v2_root = "https://feed.gws.freemyip.com/api/v2/"
    _sync_states: ClassVar[dict[tuple[str, str], _SyncState]] = {}

    def __init__(self, credentials: GkfeedCredentials) -> None:
        self.__login = credentials.login
        self.__password = credentials.password
        self._state = self._sync_states.setdefault(
            (credentials.login, credentials.password), _SyncState()
        )

    async def get_user_items(self, limit: int = 100) -> AsyncGenerator[FeedItem]:
        """Refresh metadata with v2 changes; fetch full text only for selection."""
        async with self._state.lock:
            if self._state.cursor is None:
                await self._load_initial_items(limit)
            try:
                await self._load_changes(limit)
            except aiohttp.ClientResponseError as error:
                if error.status != 400:
                    raise
                # A changed API secret invalidates previously issued cursors.
                await self._load_initial_items(limit)
                await self._load_changes(limit)

            # Preserve the existing selection window and feed grouping.
            for item in sorted(
                self._state.items.values(), key=lambda item: item.id, reverse=True
            )[:1000]:
                yield item

    async def _load_initial_items(self, limit: int) -> None:
        items: dict[int, FeedItem] = {}
        cursor = None
        anchor = None
        seen_cursors: set[str] = set()
        while True:
            data = await self._get_sync_page("sync", limit, cursor)
            if anchor is None:
                anchor = data["sync_cursor"]
                if not isinstance(anchor, str) or not anchor:
                    raise ValueError("Missing initial sync cursor")
            items.update(self._metadata_items(data["items"]))
            has_more, cursor = data["has_more"], data["next_cursor"]
            del data
            if not has_more:
                break
            if cursor in seen_cursors:
                raise ValueError("Repeated sync cursor")
            seen_cursors.add(cursor)

        self._state.items = items
        self._state.cursor = anchor

    async def _load_changes(self, limit: int) -> None:
        seen_cursors: set[str] = set()
        while True:
            data = await self._get_sync_page("changes", limit, self._state.cursor)
            items = self._metadata_items(data["upserted"])
            deleted_ids = set(data["deleted_ids"]) | {
                raw_item["id"] for raw_item in data["upserted"] if not raw_item["link"]
            }
            has_more, cursor = data["has_more"], data["next_cursor"]
            if not cursor or (has_more and cursor in seen_cursors):
                raise ValueError("Invalid change cursor")
            # No awaits between applying a page and advancing its checkpoint.
            self._state.items.update(items)
            for item_id in deleted_ids:
                self._state.items.pop(item_id, None)
            self._state.cursor = cursor
            del data
            if not has_more:
                return
            seen_cursors.add(cursor)

    async def _get_sync_page(self, route: str, limit: int, cursor: str | None) -> dict:
        params = {"limit": str(limit)}
        if cursor is not None:
            params["cursor"] = cursor
        response = await self._get_html(
            self._api_v2_root + f"items/{route}?{urlencode(params)}"
        )
        data = json.loads(response)
        if not isinstance(data["has_more"], bool) or not isinstance(
            data["next_cursor"], str
        ):
            raise TypeError("Invalid sync page")
        if data["has_more"] and (
            not data["next_cursor"] or data["next_cursor"] == cursor
        ):
            raise ValueError("Sync cursor did not advance")
        return data

    def _metadata_items(self, raw_items: list[dict]) -> dict[int, FeedItem]:
        return {
            raw_item["id"]: self._convert_raw_data_to_feed_item(
                raw_item, include_text=False
            )
            for raw_item in raw_items
            if raw_item["link"]
        }

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

    async def get_item_by_item_id(self, item_id: int) -> FeedItem:
        resp = await self._get_html(self._api_v2_root + f"items/{item_id}")
        data = json.loads(resp)
        item = data["item"]
        return self._convert_raw_data_to_feed_item(item)

    async def get_raw_item_data(self, item_id: int) -> dict:
        resp = await self._get_html(self._api_root + f"item?id={item_id}")
        return json.loads(resp)

    @staticmethod
    def _convert_raw_data_to_feed_item(
        raw_data: dict, *, include_text: bool = True
    ) -> FeedItem:
        return FeedItem(
            id=raw_data["id"],
            feed_id=raw_data["feed_id"],
            link=raw_data["link"],
            title=raw_data["title"],
            text=raw_data["text"] if include_text else "",
        )

    async def _get_soup(self, url: str) -> BeautifulSoup:
        html = await self._get_html(url)
        return BeautifulSoup(html, "xml")

    async def _get_html(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(login=self.__login, password=self.__password)
            async with session.get(url, auth=auth) as response:
                response.raise_for_status()
                return await response.read()
