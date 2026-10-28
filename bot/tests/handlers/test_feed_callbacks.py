import asyncio
import gc
import logging
import weakref
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import DeleteMessage
from aiogram.types import CallbackQuery, Chat, Message, User

from modules.feed.handlers import callbacks
from modules.feed.handlers.callbacks import ItemEventHandler
from modules.feed.ui.keyboards import FeedMarkup
from services.gkfeed import FeedItem, GkfeedAuthService, GkfeedCredentials
from services.gkfeed.api import GkfeedApi


@pytest.fixture(autouse=True)
async def deletion_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[None]:
    monkeypatch.setattr(callbacks, "_delete_tasks", set(), raising=False)
    yield
    tasks = list(callbacks._delete_tasks)
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


@pytest.fixture
def handler() -> ItemEventHandler:
    message = Message(
        message_id=7,
        date=datetime.now(UTC),
        chat=Chat(id=42, type="private"),
    )
    return ItemEventHandler(
        event=CallbackQuery(
            id="offline",
            from_user=User(id=42, is_bot=False, first_name="offline"),
            chat_instance="offline",
            message=message,
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


async def test_delete_precedes_blocked_credentials(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
) -> None:
    entered = asyncio.Event()
    release = asyncio.Event()

    async def load_credentials(user_id: int) -> GkfeedCredentials:
        entered.set()
        await release.wait()
        return GkfeedCredentials("test", "password")

    credentials.side_effect = load_credentials
    with patch.object(handler, "_send_one_feed_item", new_callable=AsyncMock) as send:
        task = asyncio.create_task(handler.handle())
        try:
            await asyncio.wait_for(entered.wait(), 1)
            telegram_delete.assert_awaited_once()
            api_delete.assert_not_awaited()
            send.assert_not_awaited()
            assert not task.done()
            release.set()
            await asyncio.wait_for(task, 1)
            await asyncio.gather(*callbacks._delete_tasks)
            api_delete.assert_awaited_once_with(11)
            send.assert_awaited_once()
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


async def test_keep_deletes_without_reading_credentials(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
) -> None:
    credentials.side_effect = AssertionError("keep does not need API credentials")
    await handler._handle_event(FeedMarkup.data.keep, 11)
    telegram_delete.assert_awaited_once()
    credentials.assert_not_awaited()
    api_delete.assert_not_awaited()
    assert not callbacks._delete_tasks


@pytest.mark.parametrize("action", [FeedMarkup.data.delete, FeedMarkup.data.keep])
async def test_old_message_is_deleted_while_next_item_is_blocked(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
    action: str,
) -> None:
    assert isinstance(handler.event, CallbackQuery)
    handler.event = handler.event.model_copy(
        update={"data": f"{FeedMarkup.prefix}:{action}:11"}
    )
    entered = asyncio.Event()
    release = asyncio.Event()
    item = FeedItem(12, 22, "https://example.invalid/next", "next", "")

    async def next_item() -> FeedItem:
        entered.set()
        await release.wait()
        return item

    with (
        patch.object(
            callbacks.GkfeedItemsPicker, "get_next_item", side_effect=next_item
        ),
        patch.object(handler, "_process_item", new_callable=AsyncMock) as process,
    ):
        task = asyncio.create_task(handler.handle())
        try:
            await asyncio.wait_for(entered.wait(), 1)
            telegram_delete.assert_awaited_once()
            process.assert_not_awaited()
            assert not task.done()
            release.set()
            await asyncio.wait_for(task, 1)
            await asyncio.gather(*callbacks._delete_tasks)
            process.assert_awaited_once_with(item)
            if action == FeedMarkup.data.delete:
                api_delete.assert_awaited_once_with(11)
            else:
                api_delete.assert_not_awaited()
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


async def test_telegram_error_prevents_db_api_and_next_item(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
) -> None:
    error = TelegramBadRequest(
        method=DeleteMessage(chat_id=42, message_id=7), message="delete failed"
    )
    telegram_delete.side_effect = error
    with (
        patch.object(handler, "_send_one_feed_item", new_callable=AsyncMock) as send,
        pytest.raises(TelegramBadRequest) as raised,
    ):
        await handler.handle()
    assert raised.value is error
    credentials.assert_not_awaited()
    api_delete.assert_not_awaited()
    send.assert_not_awaited()
    assert not callbacks._delete_tasks


async def test_db_error_propagates_after_telegram_delete(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
) -> None:
    error = ValueError("missing credentials")
    credentials.side_effect = error
    with (
        patch.object(handler, "_send_one_feed_item", new_callable=AsyncMock) as send,
        pytest.raises(ValueError) as raised,
    ):
        await handler.handle()
    assert raised.value is error
    telegram_delete.assert_awaited_once()
    api_delete.assert_not_awaited()
    send.assert_not_awaited()
    assert not callbacks._delete_tasks


@pytest.mark.parametrize("cancel_handler", [False, True])
async def test_background_delete_survives_handler_completion_or_cancellation(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
    cancel_handler: bool,
) -> None:
    entered = asyncio.Event()
    release = asyncio.Event()

    async def delete_item(item_id: int) -> None:
        entered.set()
        await release.wait()

    api_delete.side_effect = delete_item
    next_item = asyncio.Event()
    with patch.object(
        handler,
        "_send_one_feed_item",
        new=AsyncMock(side_effect=next_item.wait if cancel_handler else None),
    ):
        task = asyncio.create_task(handler.handle())
        try:
            await asyncio.wait_for(entered.wait(), 1)
            if cancel_handler:
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                await asyncio.wait_for(task, 1)
            assert len(callbacks._delete_tasks) == 1
            deletion = next(iter(callbacks._delete_tasks))
            reference = weakref.ref(deletion)
            del deletion
            gc.collect()
            assert reference() in callbacks._delete_tasks
            retained = reference()
            assert retained is not None
            assert not retained.done()
            del retained
            release.set()
            await asyncio.wait_for(asyncio.gather(*callbacks._delete_tasks), 1)
            assert not callbacks._delete_tasks
            telegram_delete.assert_awaited_once()
            api_delete.assert_awaited_once_with(11)
        finally:
            release.set()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


async def test_background_failure_logs_original_traceback(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = aiohttp.ClientConnectionError("offline delete failed")

    async def fail_delete(item_id: int) -> None:
        raise error

    api_delete.side_effect = fail_delete
    with patch.object(handler, "_send_one_feed_item", new_callable=AsyncMock) as send:
        await handler.handle()
        await asyncio.wait_for(asyncio.wait(callbacks._delete_tasks), 1)
    send.assert_awaited_once()
    assert not callbacks._delete_tasks
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.name == callbacks.__name__
    assert record.levelno == logging.ERROR
    assert record.args == (11,)
    assert record.exc_info is not None
    assert record.exc_info[1] is error
    assert record.exc_info[2] is error.__traceback__
    assert record.exc_info[2] is not None
    assert "in fail_delete" in caplog.text
    assert "ClientConnectionError: offline delete failed" in caplog.text
    assert "NoneType: None" not in caplog.text
    assert "Task exception was never retrieved" not in caplog.text
    assert "password" not in record.getMessage()


async def test_background_cancellation_is_logged_and_released(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    await handler._handle_event(FeedMarkup.data.delete, 11)
    deletion = next(iter(callbacks._delete_tasks))
    deletion.cancel()
    with pytest.raises(asyncio.CancelledError):
        await deletion
    assert not callbacks._delete_tasks
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == logging.WARNING
    assert record.args == (11,)
    assert record.exc_info is None


async def test_next_item_failure_propagates_after_deletion(
    handler: ItemEventHandler,
    telegram_delete: AsyncMock,
    credentials: AsyncMock,
    api_delete: AsyncMock,
) -> None:
    error = RuntimeError("next item failed")
    with (
        patch.object(handler, "_send_one_feed_item", new=AsyncMock(side_effect=error)),
        pytest.raises(RuntimeError) as raised,
    ):
        await handler.handle()
    await asyncio.gather(*callbacks._delete_tasks)
    assert raised.value is error
    telegram_delete.assert_awaited_once()
    api_delete.assert_awaited_once_with(11)
