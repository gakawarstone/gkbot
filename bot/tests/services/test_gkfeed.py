import asyncio
import json
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from services.gkfeed import GkfeedApi, GkfeedCredentials, GkfeedItemsPicker


@pytest.fixture(autouse=True)
def reset_feed_state() -> Iterator[None]:
    GkfeedApi._items_lock = asyncio.Lock()
    GkfeedApi._items_cache.clear()
    GkfeedItemsPicker._items_pocket.clear()
    yield
    GkfeedApi._items_cache.clear()
    GkfeedItemsPicker._items_pocket.clear()


def item_response(*item_ids: int) -> bytes:
    return json.dumps(
        {
            "items": [
                {
                    "id": item_id,
                    "feed_id": 1,
                    "link": f"https://example.invalid/{item_id}",
                    "title": f"Item {item_id}",
                    "text": f"Full text {item_id}",
                }
                for item_id in item_ids
            ]
        }
    ).encode()


async def item_ids(api: GkfeedApi, **params: int) -> list[int]:
    return [item.id async for item in api.get_user_items(**params)]


async def test_cache_is_shared_between_instances_and_expires_after_five_minutes() -> (
    None
):
    credentials = GkfeedCredentials("user", "password")
    get = AsyncMock(side_effect=[item_response(1), item_response(2)])
    with (
        patch.object(GkfeedApi, "_get_html", get),
        patch("services.gkfeed.api.monotonic", return_value=0.0) as clock,
    ):
        assert await item_ids(GkfeedApi(credentials)) == [1]
        clock.return_value = 299.0
        assert await item_ids(GkfeedApi(credentials)) == [1]
        assert get.await_count == 1
        clock.return_value = 300.0
        assert await item_ids(GkfeedApi(credentials)) == [2]
    assert get.await_count == 2
    assert all(
        call.args[0].endswith("/api/v1/get_items?limit=1000")
        for call in get.await_args_list
    )


async def test_ttl_starts_after_successful_load() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    with patch("services.gkfeed.api.monotonic", return_value=0.0) as clock:

        async def get(url: str) -> bytes:
            clock.return_value = 30.0
            return item_response(1)

        with patch.object(GkfeedApi, "_get_html", side_effect=get) as fetch:
            assert await item_ids(api) == [1]
            clock.return_value = 329.0
            assert await item_ids(api) == [1]
            fetch.assert_awaited_once()


async def test_simultaneous_same_account_calls_share_one_request() -> None:
    credentials = GkfeedCredentials("user", "password")
    started = asyncio.Event()
    release = asyncio.Event()

    async def get(url: str) -> bytes:
        started.set()
        await release.wait()
        return item_response(1)

    with patch.object(GkfeedApi, "_get_html", side_effect=get) as fetch:
        first = asyncio.create_task(item_ids(GkfeedApi(credentials)))
        await started.wait()
        second = asyncio.create_task(item_ids(GkfeedApi(credentials)))
        await asyncio.sleep(0)
        fetch.assert_awaited_once()
        release.set()
        assert await asyncio.gather(first, second) == [[1], [1]]
        fetch.assert_awaited_once()


async def test_only_one_list_request_is_active_across_all_accounts() -> None:
    active = peak = 0

    async def get(url: str) -> bytes:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        try:
            await asyncio.sleep(0)
            return item_response(1)
        finally:
            active -= 1

    with patch.object(GkfeedApi, "_get_html", side_effect=get) as fetch:
        results = await asyncio.gather(
            *(
                item_ids(GkfeedApi(GkfeedCredentials(f"user{i}", "password")))
                for i in range(5)
            )
        )
    assert results == [[1]] * 5
    assert fetch.await_count == 5
    assert peak == 1


async def test_cache_isolated_by_credentials_limit_and_cursor() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    get = AsyncMock(side_effect=[item_response(i) for i in range(1, 6)])
    with patch.object(GkfeedApi, "_get_html", get):
        assert await item_ids(api) == [1]
        assert await item_ids(GkfeedApi(GkfeedCredentials("other", "password"))) == [2]
        assert await item_ids(GkfeedApi(GkfeedCredentials("user", "new-password"))) == [
            3
        ]
        assert await item_ids(api, limit=10) == [4]
        assert await item_ids(api, cursor=7) == [5]
        assert await item_ids(api) == [1]
    assert get.await_count == 5
    assert get.await_args_list[3].args[0].endswith("get_items?limit=10")
    assert get.await_args_list[4].args[0].endswith("get_items?limit=1000&cursor=7")


@pytest.mark.parametrize(
    ("failure", "error_type"),
    [
        (aiohttp.ClientResponseError(MagicMock(), (), status=503), aiohttp.ClientError),
        (asyncio.CancelledError(), asyncio.CancelledError),
        (b"invalid JSON", ValueError),
        (b"{}", KeyError),
    ],
)
async def test_failed_load_is_not_cached_and_releases_lock(
    failure: bytes | BaseException, error_type: type[BaseException]
) -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    get = AsyncMock(side_effect=[failure, item_response(1)])
    with patch.object(GkfeedApi, "_get_html", get):
        with pytest.raises(error_type):
            await item_ids(api)
        assert not GkfeedApi._items_cache
        assert not GkfeedApi._items_lock.locked()
        assert await item_ids(api) == [1]
        assert await item_ids(api) == [1]
    assert get.await_count == 2


async def test_empty_response_is_cached() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    get = AsyncMock(return_value=item_response())
    with patch.object(GkfeedApi, "_get_html", get):
        assert await item_ids(api) == []
        assert await item_ids(api) == []
    get.assert_awaited_once()


async def test_refresh_removes_expired_entries_of_other_accounts() -> None:
    get = AsyncMock(return_value=item_response(1))
    with (
        patch.object(GkfeedApi, "_get_html", get),
        patch("services.gkfeed.api.monotonic", return_value=0.0) as clock,
    ):
        assert await item_ids(GkfeedApi(GkfeedCredentials("old", "password"))) == [1]
        clock.return_value = 300.0
        assert await item_ids(GkfeedApi(GkfeedCredentials("new", "password"))) == [1]
    assert [key[0] for key in GkfeedApi._items_cache] == ["new"]


async def test_picker_reuses_full_items_without_detail_requests() -> None:
    credentials = GkfeedCredentials("user", "password")
    get = AsyncMock(return_value=item_response(2, 1))
    with patch.object(GkfeedApi, "_get_html", get):
        first = await GkfeedItemsPicker(credentials).get_next_item()
        second = await GkfeedItemsPicker(credentials).get_next_item()
    assert first is not None and first.id == 1 and first.text == "Full text 1"
    assert second is not None and second.id == 2 and second.text == "Full text 2"
    get.assert_awaited_once()


async def test_http_error_is_checked_before_reading_body() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    response = MagicMock()
    response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        MagicMock(), (), status=503
    )
    response.read = AsyncMock()
    session = MagicMock()
    session.get.return_value.__aenter__.return_value = response
    with patch("services.gkfeed.api.aiohttp.ClientSession") as create_session:
        create_session.return_value.__aenter__.return_value = session
        with pytest.raises(aiohttp.ClientResponseError):
            await api._get_html("https://example.invalid/get_items?limit=1000")
    response.read.assert_not_awaited()
