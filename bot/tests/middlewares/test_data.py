from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, TelegramObject

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


class TimezoneHandler(UseTimeZoneHandlerExtension):
    async def handle(self) -> None:
        pass


async def test_user_context_is_shared_between_messages_and_callbacks() -> None:
    store = UserDataStore()
    middleware = UserDataMiddleware(store)
    state = FSMContext(MemoryStorage(), StorageKey(bot_id=1, chat_id=1, user_id=7))

    async def keep_session(event: TelegramObject, data: MiddlewareData) -> None:
        if "state" in data:
            await data["state"].set_state("FSM:waiting")

    message = MagicMock(spec=Message, from_user=MagicMock(id=7))
    callback = MagicMock(spec=CallbackQuery, from_user=MagicMock(id=7))
    other_user = MagicMock(spec=Message, from_user=MagicMock(id=8))
    message_data: MiddlewareData = {"state": state}
    callback_data: MiddlewareData = {"state": state}
    other_data: MiddlewareData = {}

    await middleware(keep_session, message, message_data)
    user_data = require_user_data(message_data)
    user_data["tz"] = timedelta(hours=3)
    await middleware(keep_session, callback, callback_data)
    await middleware(keep_session, other_user, other_data)

    assert require_user_data(callback_data).get("tz") == timedelta(hours=3)
    assert require_user_data(other_data).get("tz") is None
    store.clear()


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
