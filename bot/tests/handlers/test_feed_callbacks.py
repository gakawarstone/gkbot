import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import aiohttp
import pytest
from aiogram.types import CallbackQuery, Chat, Message, User

from modules.feed.handlers.callbacks import ItemEventHandler
from modules.feed.ui.keyboards import FeedMarkup
from services.gkfeed import GkfeedAuthService, GkfeedCredentials
from services.gkfeed.api import GkfeedApi


@pytest.fixture
def handler() -> ItemEventHandler:
    return ItemEventHandler(
        event=CallbackQuery(
            id="offline",
            from_user=User(id=42, is_bot=False, first_name="offline"),
            chat_instance="offline",
            message=Message(
                message_id=7,
                date=datetime.now(UTC),
                chat=Chat(id=42, type="private"),
            ),
            data=f"{FeedMarkup.prefix}:{FeedMarkup.data.delete}:11",
        )
    )


@pytest.fixture
def telegram_delete(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    delete = AsyncMock(return_value=True)
    monkeypatch.setattr(Message, "delete", delete)
    return delete


@pytest.fixture
def credentials(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    credentials = AsyncMock(return_value=GkfeedCredentials("test", "password"))
    monkeypatch.setattr(GkfeedAuthService, "get_credentials", credentials)
    return credentials


@pytest.fixture
def api_delete(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    delete = AsyncMock()
    monkeypatch.setattr(GkfeedApi, "delete_item_by_id", delete)
    return delete


@pytest.fixture
def send_next(handler: ItemEventHandler, monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    send = AsyncMock()
    monkeypatch.setattr(handler, "_send_one_feed_item", send)
    return send


@pytest.mark.parametrize("stage", ["credentials", "api", "next"])
async def test_telegram_delete_precedes_slow_work(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
    send_next: AsyncMock,
    stage: str,
) -> None:
    entered = asyncio.Event()
    release = asyncio.Event()

    async def wait_for_release(*args: object) -> GkfeedCredentials:
        entered.set()
        await release.wait()
        return GkfeedCredentials("test", "password")

    operations = {"credentials": credentials, "api": api_delete, "next": send_next}
    operations[stage].side_effect = wait_for_release
    task = asyncio.create_task(handler.handle())
    try:
        await asyncio.wait_for(entered.wait(), 1)
        telegram_delete.assert_awaited_once()
        assert not task.done()
        if stage == "credentials":
            api_delete.assert_not_awaited()
        if stage != "next":
            send_next.assert_not_awaited()
        release.set()
        await asyncio.wait_for(task, 1)
        credentials.assert_awaited_once_with(42)
        api_delete.assert_awaited_once_with(11)
        send_next.assert_awaited_once()
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def test_keep_deletes_without_api_credentials(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
) -> None:
    await handler._handle_event(FeedMarkup.data.keep, 11)
    telegram_delete.assert_awaited_once()
    credentials.assert_not_awaited()
    api_delete.assert_not_awaited()


@pytest.mark.parametrize("stage", ["telegram", "credentials", "api", "next"])
async def test_failure_propagates_and_stops_later_operations(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
    send_next: AsyncMock,
    stage: str,
) -> None:
    operations = [telegram_delete, credentials, api_delete, send_next]
    failed_index = ["telegram", "credentials", "api", "next"].index(stage)
    error = aiohttp.ClientConnectionError("offline failure")
    operations[failed_index].side_effect = error
    with pytest.raises(aiohttp.ClientConnectionError) as raised:
        await handler.handle()
    assert raised.value is error
    assert raised.value.__traceback__ is not None
    for operation in operations[: failed_index + 1]:
        operation.assert_awaited_once()
    for operation in operations[failed_index + 1 :]:
        operation.assert_not_awaited()
