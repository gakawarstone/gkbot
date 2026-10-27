import asyncio
import json
import threading
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, Mock
from urllib.parse import parse_qs, urlsplit

import aiohttp
import pytest

from services.gkfeed import GkfeedItemsPicker
from services.gkfeed import api as api_module
from services.gkfeed._decoder import FeedDecoder
from services.gkfeed._types import FeedItem, FeedItemSummary, GkfeedCredentials
from services.gkfeed.api import GkfeedApi


def payload() -> bytes:
    return json.dumps(
        {
            "items": [
                {
                    "id": 3,
                    "feed_id": 10,
                    "link": "three",
                    "title": "3",
                    "date": "2026-10-26T12:00:00Z",
                },
                {
                    "id": 1,
                    "feed_id": 10,
                    "link": "one",
                    "title": "Заголовок",
                    "date": "2026-10-26T10:00:00Z",
                },
                {"link": ""},
                {
                    "id": 2,
                    "feed_id": 20,
                    "link": "two",
                    "title": "2",
                    "date": "2026-10-26T11:00:00Z",
                },
            ]
        }
    ).encode()


@pytest.fixture
async def api(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[GkfeedApi]:
    decoder = FeedDecoder()
    monkeypatch.setattr(GkfeedApi, "_items_decoder", decoder)
    monkeypatch.setattr(GkfeedApi, "_items_cache", {})
    monkeypatch.setattr(GkfeedApi, "_items_lock", asyncio.Lock())
    monkeypatch.setattr(GkfeedItemsPicker, "_items_pocket", {})
    monkeypatch.setattr(GkfeedApi, "_get_html", AsyncMock(return_value=payload()))
    try:
        yield GkfeedApi(GkfeedCredentials("test", "password"))
    finally:
        await GkfeedApi.on_shutdown()


async def consume(
    api: GkfeedApi, limit: int = 1000, cursor: int | None = None
) -> list[FeedItemSummary]:
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
    assert cold[1].date == "2026-10-26T10:00:00Z"
    assert all(not hasattr(item, "text") for item in cold)
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
    read.assert_awaited_once_with(
        api._api_root + f"get_items?view=summary&limit=17{suffix}"
    )
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

    def decode(body: bytes) -> list[FeedItemSummary]:
        nonlocal submissions
        submissions += 1
        entered.set()
        assert release.wait(5)
        return [FeedItemSummary(1, 10, "one", "title", "2026-10-26T10:00:00Z")]

    monkeypatch.setattr(api._items_decoder, "_decode", decode)
    first = asyncio.create_task(consume(api))
    waiters: list[asyncio.Task[list[FeedItemSummary]]] = []
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


async def test_picker_order_and_pocket_are_preserved(api: GkfeedApi) -> None:
    read = api._get_html
    assert isinstance(read, AsyncMock)

    async def fetch(url: str) -> bytes:
        if urlsplit(url).path.endswith("get_items"):
            return payload()
        item_id = int(parse_qs(urlsplit(url).query)["id"][0])
        summary = next(
            item for item in json.loads(payload())["items"] if item.get("id") == item_id
        )
        return json.dumps({"item": {**summary, "text": "Полный текст"}}).encode()

    read.side_effect = fetch
    picker = GkfeedItemsPicker(GkfeedCredentials("test", "password"))
    picked = [await picker.get_next_item() for _ in range(5)]
    assert [item.id if item else None for item in picked] == [1, 3, 2, None, 1]
    assert all(
        isinstance(item, FeedItem) and item.text == "Полный текст"
        for item in picked
        if item
    )
    assert [call.args[0] for call in read.await_args_list] == [
        api._api_root + "get_items?view=summary&limit=1000",
        api._api_root + "item?id=1",
        api._api_root + "item?id=3",
        api._api_root + "item?id=2",
        api._api_root + "item?id=1",
    ]


async def test_picker_keeps_the_1000_item_window(
    api: GkfeedApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    read = api._get_html
    assert isinstance(read, AsyncMock)
    read.return_value = json.dumps(
        {
            "items": [
                {
                    "id": item_id,
                    "feed_id": 10,
                    "link": str(item_id),
                    "title": str(item_id),
                    "date": "2026-10-26T10:00:00Z",
                }
                for item_id in range(2000, 1000, -1)
            ],
            "next_cursor": 1001,
        }
    ).encode()
    detail = AsyncMock(return_value=FeedItem(1001, 10, "1001", "1001", "text"))
    monkeypatch.setattr(GkfeedApi, "get_item_by_item_id", detail)
    picker = GkfeedItemsPicker(GkfeedCredentials("test", "password"))
    item = await picker.get_next_item()
    assert item is not None and item.id == 1001
    detail.assert_awaited_once_with(1001)
    read.assert_awaited_once_with(api._api_root + "get_items?view=summary&limit=1000")


async def test_picker_filters_summaries_before_loading_detail(
    api: GkfeedApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    detail = AsyncMock(return_value=FeedItem(2, 20, "two", "2", "text"))
    monkeypatch.setattr(GkfeedApi, "get_item_by_item_id", detail)
    picker = GkfeedItemsPicker(GkfeedCredentials("test", "password"))
    assert (
        await picker.get_next_item(lambda item: item.feed_id == 20)
        == detail.return_value
    )
    detail.assert_awaited_once_with(2)


async def test_concurrent_pickers_do_not_return_the_same_item(
    api: GkfeedApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    both_loading = asyncio.Event()
    loading = 0

    async def fetch_detail(item_id: int) -> FeedItem:
        nonlocal loading
        if item_id == 1:
            loading += 1
            if loading == 2:
                both_loading.set()
            await both_loading.wait()
        return FeedItem(item_id, 10, str(item_id), str(item_id), "text")

    detail = AsyncMock(side_effect=fetch_detail)
    monkeypatch.setattr(GkfeedApi, "get_item_by_item_id", detail)
    credentials = GkfeedCredentials("test", "password")
    first, second = await asyncio.gather(
        GkfeedItemsPicker(credentials).get_next_item(),
        GkfeedItemsPicker(credentials).get_next_item(),
    )
    assert first is not None and second is not None
    assert {first.id, second.id} == {1, 3}
    assert [call.args[0] for call in detail.await_args_list] == [1, 1, 3]


@pytest.mark.parametrize("all_deleted", [False, True])
async def test_deleted_candidates_are_not_saved_or_retried_in_one_pick(
    api: GkfeedApi, all_deleted: bool
) -> None:
    not_found = aiohttp.ClientResponseError(
        request_info=Mock(spec=aiohttp.RequestInfo), history=(), status=404
    )
    read = api._get_html
    assert isinstance(read, AsyncMock)
    full_item = {**json.loads(payload())["items"][0], "text": "text"}
    read.side_effect = (
        [payload(), not_found, not_found, not_found]
        if all_deleted
        else [payload(), not_found, json.dumps({"item": full_item}).encode()]
    )
    picker = GkfeedItemsPicker(GkfeedCredentials("test", "password"))
    item = await picker.get_next_item()
    expected_ids = [1, 3, 2] if all_deleted else [1, 3]
    assert [call.args[0] for call in read.await_args_list[1:]] == [
        api._api_root + f"item?id={item_id}" for item_id in expected_ids
    ]
    assert picker._items_pocket["test"] == (set() if all_deleted else {3})
    assert (item.id if item else None) == (None if all_deleted else 3)


@pytest.mark.parametrize(
    "failure",
    [
        aiohttp.ClientResponseError(
            request_info=Mock(spec=aiohttp.RequestInfo), history=(), status=500
        ),
        aiohttp.ClientResponseError(
            request_info=Mock(spec=aiohttp.RequestInfo), history=(), status=401
        ),
        aiohttp.ClientConnectionError("detail connection failure"),
        KeyError("text"),
    ],
)
async def test_detail_failure_does_not_save_candidate(
    api: GkfeedApi, failure: Exception
) -> None:
    read = api._get_html
    assert isinstance(read, AsyncMock)
    read.side_effect = [payload(), failure]
    picker = GkfeedItemsPicker(GkfeedCredentials("test", "password"))
    with pytest.raises(type(failure)):
        await picker.get_next_item()
    assert picker._items_pocket["test"] == set()
    assert read.await_count == 2
    read.assert_awaited_with(api._api_root + "item?id=1")


async def test_detail_requires_text(api: GkfeedApi) -> None:
    read = api._get_html
    assert isinstance(read, AsyncMock)
    raw_item = json.loads(payload())["items"][0]
    read.return_value = json.dumps({"item": raw_item}).encode()
    with pytest.raises(KeyError, match="text"):
        await api.get_item_by_item_id(3)
    read.return_value = json.dumps({"item": {**raw_item, "text": ""}}).encode()
    item = await api.get_item_by_item_id(3)
    assert item is not None and item.text == ""
