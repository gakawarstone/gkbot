import asyncio
import json
import threading
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import aiohttp
import pytest

from services.gkfeed import GkfeedItemsPicker
from services.gkfeed import api as api_module
from services.gkfeed._decoder import FeedDecoder
from services.gkfeed._types import FeedItem, GkfeedCredentials
from services.gkfeed.api import GkfeedApi


def payload() -> bytes:
    return json.dumps(
        {
            "items": [
                {"id": 3, "feed_id": 10, "link": "three", "title": "3", "text": ""},
                {
                    "id": 1,
                    "feed_id": 10,
                    "link": "one",
                    "title": "Заголовок",
                    "text": '<img src="data:image/png;base64,YWJj"> текст',
                },
                {"link": ""},
                {"id": 2, "feed_id": 20, "link": "two", "title": "2", "text": ""},
            ]
        }
    ).encode()


@pytest.fixture
async def api(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[GkfeedApi]:
    decoder = FeedDecoder()
    monkeypatch.setattr(GkfeedApi, "_items_decoder", decoder)
    monkeypatch.setattr(GkfeedApi, "_items_cache", {})
    monkeypatch.setattr(GkfeedApi, "_items_lock", asyncio.Lock())
    monkeypatch.setattr(GkfeedApi, "_get_html", AsyncMock(return_value=payload()))
    try:
        yield GkfeedApi(GkfeedCredentials("test", "password"))
    finally:
        await GkfeedApi.on_shutdown()


async def consume(
    api: GkfeedApi, limit: int = 1000, cursor: int | None = None
) -> list[FeedItem]:
    return [item async for item in api.get_user_items(limit, cursor)]


async def test_cold_hot_cache_contract_and_ttl(
    api: GkfeedApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = [100.0]
    monkeypatch.setattr(api_module, "monotonic", lambda: now[0])
    await GkfeedApi.on_startup()
    cold = await consume(api)
    assert [item.id for item in cold] == [3, 1, 2]
    assert cold[1].title == "Заголовок"
    assert cold[1].text == '<img src="data:image/png;base64,YWJj"> текст'
    read = api._get_html
    assert isinstance(read, AsyncMock)
    now[0] = 399.9
    hot = await consume(api)
    assert all(left is right for left, right in zip(cold, hot, strict=True))
    read.assert_awaited_once()
    now[0] = 400.0
    assert await consume(api) == cold
    assert read.await_count == 2


@pytest.mark.parametrize("cursor", [None, 0, 42])
async def test_query_and_cache_keys(api: GkfeedApi, cursor: int | None) -> None:
    await consume(api, limit=17, cursor=cursor)
    read = api._get_html
    assert isinstance(read, AsyncMock)
    suffix = f"&cursor={cursor}" if cursor else ""
    read.assert_awaited_once_with(api._api_root + f"get_items?limit=17{suffix}")
    await consume(api, limit=17, cursor=cursor)
    read.assert_awaited_once()
    await consume(api, limit=18, cursor=cursor)
    other_user = GkfeedApi(GkfeedCredentials("other", "password"))
    await consume(other_user, limit=17, cursor=cursor)
    other_password = GkfeedApi(GkfeedCredentials("test", "other"))
    await consume(other_password, limit=17, cursor=cursor)
    assert read.await_count == 4


async def test_same_and_different_key_misses_remain_serialized(api: GkfeedApi) -> None:
    read = api._get_html
    assert isinstance(read, AsyncMock)
    entered = asyncio.Event()
    release = asyncio.Event()

    async def fetch(url: str) -> bytes:
        entered.set()
        await release.wait()
        return payload()

    read.side_effect = fetch
    first = asyncio.create_task(consume(api))
    await entered.wait()
    same = asyncio.create_task(consume(api))
    different = asyncio.create_task(consume(api, cursor=42))
    await asyncio.sleep(0)
    assert read.await_count == 1
    release.set()
    results = await asyncio.gather(first, same, different)
    assert results[0] == results[1] == results[2]
    assert read.await_count == 2


async def test_cancelled_fetch_does_not_cache_or_hold_lock(api: GkfeedApi) -> None:
    read = api._get_html
    assert isinstance(read, AsyncMock)
    entered = asyncio.Event()

    async def fetch(url: str) -> bytes:
        entered.set()
        await asyncio.Event().wait()
        return payload()

    read.side_effect = fetch
    first = asyncio.create_task(consume(api))
    await entered.wait()
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    assert not api._items_cache
    read.side_effect = None
    assert len(await consume(api)) == 3


async def test_cancelled_decode_does_not_queue_jobs_or_poison_single_flight(
    api: GkfeedApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    entered = threading.Event()
    release = threading.Event()
    submissions = 0

    def decode(_function: object, body: bytes) -> list[FeedItem]:
        nonlocal submissions
        submissions += 1
        entered.set()
        assert release.wait(5)
        return [FeedItem(1, 10, "one", "title", "text")]

    monkeypatch.setattr(api._items_decoder, "_execute", decode)
    first = asyncio.create_task(consume(api))
    waiters: list[asyncio.Task[list[FeedItem]]] = []
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        assert not api._items_cache
        waiters = [asyncio.create_task(consume(api)) for _ in range(10)]
        await asyncio.sleep(0)
        assert submissions == 1
        read = api._get_html
        assert isinstance(read, AsyncMock)
        assert read.await_count == 2
        release.set()
        results = await asyncio.gather(*waiters)
        assert all(result == results[0] for result in results)
        assert submissions == 2
        assert read.await_count == 2
    finally:
        release.set()
        await asyncio.gather(first, *waiters, return_exceptions=True)


@pytest.mark.parametrize("body", [b"invalid json", b"{}", b'{"items":[{"id":1}]}'])
async def test_decode_error_leaves_cache_empty(api: GkfeedApi, body: bytes) -> None:
    read = api._get_html
    assert isinstance(read, AsyncMock)
    read.return_value = body
    with pytest.raises((json.JSONDecodeError, KeyError)):
        await consume(api)
    assert not api._items_cache
    read.return_value = payload()
    assert len(await consume(api)) == 3


async def test_http_error_is_preserved(api: GkfeedApi) -> None:
    read = api._get_html
    assert isinstance(read, AsyncMock)
    read.side_effect = aiohttp.ClientConnectionError("test connection failure")
    with pytest.raises(aiohttp.ClientConnectionError):
        await consume(api)
    assert not api._items_cache


async def test_empty_feed_is_cached(api: GkfeedApi) -> None:
    read = api._get_html
    assert isinstance(read, AsyncMock)
    read.return_value = b'{"items":[{"link":""}]}'
    assert await consume(api) == []
    assert await consume(api) == []
    read.assert_awaited_once()


async def test_picker_order_and_pocket_are_preserved(
    api: GkfeedApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(GkfeedItemsPicker, "_items_pocket", {})
    picker = GkfeedItemsPicker(GkfeedCredentials("test", "password"))
    picked = [await picker.get_next_item() for _ in range(5)]
    assert [item.id if item else None for item in picked] == [1, 3, 2, None, 1]
    read = api._get_html
    assert isinstance(read, AsyncMock)
    read.assert_awaited_once()
