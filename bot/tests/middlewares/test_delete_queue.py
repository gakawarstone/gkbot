from collections.abc import Sequence
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramUnauthorizedError,
)
from aiogram.types import Message, TelegramObject

from middlewares.data import MiddlewareData, MiddlewareHandler, require_user_data
from middlewares.delete_queue import DeleteQueueMiddleware

UNDELETABLE_ERRORS = (
    TelegramBadRequest,
    TelegramNotFound,
    TelegramForbiddenError,
    TelegramUnauthorizedError,
)


def make_message(delete_side_effect: Any = None) -> AsyncMock:
    message = AsyncMock()
    message.delete = AsyncMock(side_effect=delete_side_effect)
    return message


def make_telegram_error(error_cls: type[TelegramAPIError]) -> TelegramAPIError:
    return error_cls(method=MagicMock(), message="message to delete not found")


@pytest.fixture
def middleware() -> DeleteQueueMiddleware:
    return DeleteQueueMiddleware()


@pytest.fixture
def handler() -> AsyncMock:
    return AsyncMock(return_value="ok")


async def run(
    middleware: DeleteQueueMiddleware,
    queue: Sequence[Message],
    handler: MiddlewareHandler,
) -> tuple[Any, MiddlewareData]:
    data: MiddlewareData = {"data": {"delete_queue": list(queue)}}
    result = await middleware(handler, MagicMock(), data)
    return result, data


async def test_clears_queue_on_success(
    middleware: DeleteQueueMiddleware, handler: AsyncMock
) -> None:
    messages = [make_message(), make_message()]

    result, data = await run(middleware, messages, handler)

    assert result == "ok"
    for message in messages:
        message.delete.assert_awaited_once()
    assert require_user_data(data)["delete_queue"] == []


@pytest.mark.parametrize("error_cls", UNDELETABLE_ERRORS)
async def test_poison_message_does_not_block_queue(
    middleware: DeleteQueueMiddleware,
    handler: AsyncMock,
    error_cls: type[TelegramAPIError],
) -> None:
    poison = make_message(make_telegram_error(error_cls))
    healthy = make_message()

    result, data = await run(middleware, [poison, healthy], handler)

    assert result == "ok"
    poison.delete.assert_awaited_once()
    healthy.delete.assert_awaited_once()
    assert require_user_data(data)["delete_queue"] == []


async def test_subsequent_update_does_not_retry_poison_message(
    middleware: DeleteQueueMiddleware, handler: AsyncMock
) -> None:
    poison = make_message(make_telegram_error(TelegramBadRequest))

    _, data = await run(middleware, [poison], handler)
    await run(middleware, require_user_data(data)["delete_queue"], handler)

    poison.delete.assert_awaited_once()
    assert handler.await_count == 2


async def test_new_entries_added_during_handling_are_preserved(
    middleware: DeleteQueueMiddleware,
) -> None:
    old, new = make_message(), make_message()

    async def handler(event: TelegramObject, handler_data: MiddlewareData) -> str:
        require_user_data(handler_data)["delete_queue"].append(new)
        return "ok"

    result, data = await run(middleware, [old], handler)

    assert result == "ok"
    old.delete.assert_awaited_once()
    new.delete.assert_not_awaited()
    assert require_user_data(data)["delete_queue"] == [new]


async def test_unexpected_error_detaches_queue_but_propagates(
    middleware: DeleteQueueMiddleware, handler: AsyncMock
) -> None:
    broken = make_message(RuntimeError("boom"))
    data: MiddlewareData = {"data": {"delete_queue": [broken]}}

    with pytest.raises(RuntimeError, match="boom"):
        await middleware(handler, MagicMock(), data)

    handler.assert_not_awaited()
    assert require_user_data(data)["delete_queue"] == []
