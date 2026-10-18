import asyncio
import json
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import aiohttp
import pytest

from services.gkfeed import GkfeedApi, GkfeedCredentials, GkfeedItemsPicker


@pytest.fixture(autouse=True)
def reset_feed_state() -> Iterator[None]:
    GkfeedApi._sync_states.clear()
    GkfeedItemsPicker._items_pocket.clear()
    yield
    GkfeedApi._sync_states.clear()
    GkfeedItemsPicker._items_pocket.clear()


def raw_item(item_id: int, feed_id: int = 1, text: str = "full text") -> dict:
    return {
        "id": item_id,
        "feed_id": feed_id,
        "link": f"https://example.invalid/{item_id}",
        "title": f"Item {item_id}",
        "text": text,
    }


def initial_page(items: list[dict], cursor: str = "", anchor: str = "anchor") -> bytes:
    return json.dumps(
        {
            "items": items,
            "next_cursor": cursor,
            "has_more": bool(cursor),
            "sync_cursor": anchor,
        }
    ).encode()


def changes_page(
    items: list[dict] | None = None,
    deleted: list[int] | None = None,
    cursor: str = "after",
    has_more: bool = False,
) -> bytes:
    return json.dumps(
        {
            "upserted": items or [],
            "deleted_ids": deleted or [],
            "next_cursor": cursor,
            "has_more": has_more,
        }
    ).encode()


def http_error(status: int) -> aiohttp.ClientResponseError:
    return aiohttp.ClientResponseError(MagicMock(), (), status=status)


async def item_ids(api: GkfeedApi) -> list[int]:
    return [item.id async for item in api.get_user_items()]


async def test_sync_paginates_short_pages_and_keeps_first_anchor() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    get = AsyncMock(
        side_effect=[
            initial_page([], cursor="page+/=", anchor="first+/="),
            initial_page([raw_item(2)], anchor="different-token"),
            changes_page([raw_item(3)], cursor="delta", has_more=True),
            changes_page(deleted=[2], cursor="final"),
        ]
    )
    with patch.object(GkfeedApi, "_get_html", get):
        assert await item_ids(api) == [3]

    urls = [call.args[0] for call in get.await_args_list]
    assert [urlsplit(url).path for url in urls] == [
        "/api/v2/items/sync",
        "/api/v2/items/sync",
        "/api/v2/items/changes",
        "/api/v2/items/changes",
    ]
    params = [parse_qs(urlsplit(url).query) for url in urls]
    assert all(query["limit"] == ["100"] for query in params)
    assert params[1]["cursor"] == ["page+/="]
    assert params[2]["cursor"] == ["first+/="]
    assert params[3]["cursor"] == ["delta"]
    assert api._state.cursor == "final"
    assert api._state.items[3].text == ""


async def test_new_clients_reuse_changes_and_fetch_selected_detail() -> None:
    credentials = GkfeedCredentials("user", "password")
    get = AsyncMock(
        side_effect=[
            initial_page([raw_item(2), raw_item(1)]),
            changes_page(cursor="first"),
            json.dumps({"item": raw_item(1)}).encode(),
            changes_page([raw_item(2, text="updated")], deleted=[1], cursor="second"),
            json.dumps({"item": raw_item(2, text="updated")}).encode(),
        ]
    )
    with patch.object(GkfeedApi, "_get_html", get):
        first = await GkfeedItemsPicker(credentials).get_next_item()
        second = await GkfeedItemsPicker(credentials).get_next_item()

    assert first is not None and first.id == 1 and first.text == "full text"
    assert second is not None and second.id == 2 and second.text == "updated"
    urls = [call.args[0] for call in get.await_args_list]
    assert sum("/items/sync?" in url for url in urls) == 1
    assert urls[2].endswith("/api/v2/items/1")
    assert urls[4].endswith("/api/v2/items/2")
    assert GkfeedApi(credentials)._state.items[2].text == ""


async def test_failed_changes_resume_last_applied_page() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    get = AsyncMock(
        side_effect=[
            initial_page([raw_item(1)]),
            changes_page([raw_item(2)], cursor="committed", has_more=True),
            http_error(503),
            changes_page(deleted=[1], cursor="committed"),
        ]
    )
    with patch.object(GkfeedApi, "_get_html", get):
        with pytest.raises(aiohttp.ClientResponseError):
            await item_ids(api)
        assert api._state.cursor == "committed"
        assert await item_ids(api) == [2]
    assert get.await_args_list[-1].args[0].endswith("cursor=committed")


async def test_incomplete_initial_sync_restarts_without_partial_cache() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    get = AsyncMock(
        side_effect=[
            initial_page([raw_item(1)], cursor="page"),
            asyncio.CancelledError(),
            initial_page([raw_item(2)]),
            changes_page(),
        ]
    )
    with patch.object(GkfeedApi, "_get_html", get):
        with pytest.raises(asyncio.CancelledError):
            await item_ids(api)
        assert api._state.cursor is None and not api._state.items
        assert await item_ids(api) == [2]
    assert "cursor=" not in get.await_args_list[2].args[0]


@pytest.mark.parametrize("status", [400, 401])
async def test_invalid_cursor_resyncs_once_but_auth_failure_does_not(
    status: int,
) -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    get = AsyncMock(
        side_effect=[
            initial_page([raw_item(1)]),
            changes_page(),
            http_error(status),
            initial_page([raw_item(2)]),
            changes_page(cursor="new"),
        ]
    )
    with patch.object(GkfeedApi, "_get_html", get):
        assert await item_ids(api) == [1]
        if status == 400:
            assert await item_ids(api) == [2]
            assert api._state.cursor == "new"
        else:
            with pytest.raises(aiohttp.ClientResponseError):
                await item_ids(api)
            assert get.await_count == 3


async def test_same_account_sync_is_serial_and_credentials_are_isolated() -> None:
    credentials = GkfeedCredentials("user", "password")
    api = GkfeedApi(credentials)
    other = GkfeedApi(credentials)
    assert GkfeedApi(GkfeedCredentials("other", "password"))._state is not api._state
    assert GkfeedApi(GkfeedCredentials("user", "new-password"))._state is not api._state
    started = asyncio.Event()
    release = asyncio.Event()
    calls: list[str] = []

    async def get(url: str) -> bytes:
        calls.append(url)
        if "/items/sync?" in url:
            started.set()
            await release.wait()
            return initial_page([raw_item(1)])
        return changes_page()

    with patch.object(GkfeedApi, "_get_html", side_effect=get):
        first = asyncio.create_task(item_ids(api))
        await started.wait()
        second = asyncio.create_task(item_ids(other))
        await asyncio.sleep(0)
        assert len(calls) == 1
        release.set()
        assert await asyncio.gather(first, second) == [[1], [1]]
    assert sum("/items/sync?" in url for url in calls) == 1


async def test_repeating_cursor_is_rejected_without_advancing_checkpoint() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    get = AsyncMock(
        side_effect=[
            initial_page([]),
            changes_page([raw_item(1)], cursor="anchor", has_more=True),
        ]
    )
    with patch.object(GkfeedApi, "_get_html", get), pytest.raises(ValueError):
        await item_ids(api)
    assert api._state.cursor == "anchor"
    assert not api._state.items


async def test_deleted_detail_is_skipped_and_transient_failure_releases_reservation() -> (
    None
):
    credentials = GkfeedCredentials("user", "password")
    get = AsyncMock(
        side_effect=[
            initial_page([raw_item(1), raw_item(2)]),
            changes_page(),
            http_error(404),
            http_error(503),
            changes_page(deleted=[1]),
            json.dumps({"item": raw_item(2)}).encode(),
        ]
    )
    with patch.object(GkfeedApi, "_get_html", get):
        with pytest.raises(aiohttp.ClientResponseError):
            await GkfeedItemsPicker(credentials).get_next_item()
        assert 2 not in GkfeedItemsPicker._items_pocket["user"]
        item = await GkfeedItemsPicker(credentials).get_next_item()
    assert item is not None and item.id == 2


async def test_metadata_window_and_feed_order_match_existing_picker() -> None:
    credentials = GkfeedCredentials("user", "password")
    get = AsyncMock(
        side_effect=[
            initial_page([raw_item(i, i % 2) for i in range(1, 1002)]),
            changes_page(),
            json.dumps({"item": raw_item(2, 0)}).encode(),
        ]
    )
    with patch.object(GkfeedApi, "_get_html", get):
        item = await GkfeedItemsPicker(credentials).get_next_item()
    assert item is not None and item.id == 2


async def test_unlinked_upsert_removes_previous_metadata() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    unlinked = raw_item(1)
    unlinked["link"] = ""
    get = AsyncMock(side_effect=[initial_page([raw_item(1)]), changes_page([unlinked])])
    with patch.object(GkfeedApi, "_get_html", get):
        assert await item_ids(api) == []


async def test_malformed_change_does_not_commit_any_part_of_page() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    malformed = raw_item(3)
    malformed.pop("title")
    get = AsyncMock(
        side_effect=[
            initial_page([raw_item(1)]),
            changes_page([raw_item(2), malformed], deleted=[1], cursor="bad-page"),
        ]
    )
    with patch.object(GkfeedApi, "_get_html", get), pytest.raises(KeyError):
        await item_ids(api)
    assert api._state.cursor == "anchor"
    assert set(api._state.items) == {1}


async def test_http_error_is_checked_before_reading_body() -> None:
    api = GkfeedApi(GkfeedCredentials("user", "password"))
    response = MagicMock()
    response.raise_for_status.side_effect = http_error(503)
    response.read = AsyncMock()
    session = MagicMock()
    session.get.return_value.__aenter__.return_value = response
    with patch("services.gkfeed.api.aiohttp.ClientSession") as create_session:
        create_session.return_value.__aenter__.return_value = session
        with pytest.raises(aiohttp.ClientResponseError):
            await api._get_html("https://example.invalid/items/changes")
    response.read.assert_not_awaited()
