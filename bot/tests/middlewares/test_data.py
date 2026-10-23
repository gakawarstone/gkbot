from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, TelegramObject

from extensions.handlers.callback.base import BaseHandler as CallbackHandler
from extensions.handlers.message.base import BaseHandler as MessageHandler
from extensions.handlers.message.use_timezone_extension import (
    UseTimeZoneHandlerExtension,
)
from middlewares.data import MiddlewareData, UserData, require_user_data
from middlewares.user_data import UserDataMiddleware
from middlewares.user_data_store import UserDataStore


class ConcreteMessageHandler(MessageHandler):
    async def handle(self) -> None:
        pass


class ConcreteCallbackHandler(CallbackHandler):
    async def handle(self) -> None:
        pass


class TimezoneHandler(UseTimeZoneHandlerExtension):
    async def handle(self) -> None:
        pass


async def test_user_context_is_shared_between_messages_and_callbacks() -> None:
    store = UserDataStore()
    middleware = UserDataMiddleware(store)
    state = FSMContext(MemoryStorage(), StorageKey(bot_id=1, chat_id=1, user_id=7))

    async def keep_session(event: TelegramObject, data: MiddlewareData) -> str:
        if "state" in data:
            await data["state"].set_state("FSM:waiting")
        return "handled"

    handler = AsyncMock(side_effect=keep_session)
    message = MagicMock(spec=Message, from_user=MagicMock(id=7))
    callback = MagicMock(spec=CallbackQuery, from_user=MagicMock(id=7))
    other_user = MagicMock(spec=Message, from_user=MagicMock(id=8))
    message_data: MiddlewareData = {"state": state}
    callback_data: MiddlewareData = {"state": state}
    other_data: MiddlewareData = {}

    assert await middleware(handler, message, message_data) == "handled"
    user_data = require_user_data(message_data)
    assert user_data == {"delete_queue": []}
    user_data["tz"] = timedelta(hours=3)
    await middleware(handler, callback, callback_data)
    await middleware(handler, other_user, other_data)

    assert require_user_data(callback_data) is user_data
    assert require_user_data(callback_data).get("tz") == timedelta(hours=3)
    assert require_user_data(other_data) == {"delete_queue": []}
    assert (
        require_user_data(other_data)["delete_queue"] is not user_data["delete_queue"]
    )
    store.clear()


@pytest.mark.parametrize(
    "handler_type", [ConcreteMessageHandler, ConcreteCallbackHandler]
)
def test_class_handlers_keep_injected_dependencies(
    handler_type: type[ConcreteMessageHandler] | type[ConcreteCallbackHandler],
) -> None:
    data: UserData = {"delete_queue": []}
    state = MagicMock()
    handler = handler_type(MagicMock(), data=data, state=state)

    assert handler.user_data is data
    assert handler.state is state
    assert handler.data["data"] is data
    assert handler.data["state"] is state


def test_missing_dependencies_have_explicit_errors() -> None:
    handler = ConcreteMessageHandler(MagicMock())
    with pytest.raises(RuntimeError, match="UserDataMiddleware"):
        _ = handler.user_data
    with pytest.raises(RuntimeError, match="FSM middleware"):
        _ = handler.state


@pytest.mark.parametrize(
    "data", [{"delete_queue": []}, {"delete_queue": [], "tz": None}]
)
def test_timezone_handler_requires_a_populated_timezone(data: UserData) -> None:
    handler = TimezoneHandler(MagicMock(), data=data)
    with pytest.raises(RuntimeError, match="requires a timezone"):
        _ = handler.tz


def test_timezone_handler_returns_injected_offset() -> None:
    offset = timedelta(hours=3)
    handler = TimezoneHandler(MagicMock(), data={"delete_queue": [], "tz": offset})
    assert handler.tz == offset


def test_timezone_flag_survives_class_handler_inheritance() -> None:
    handler = HandlerObject(callback=TimezoneHandler)
    assert handler.flags["require_timezone"] is True
