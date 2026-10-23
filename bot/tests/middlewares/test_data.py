from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.types import CallbackQuery, Message

from extensions.handlers.callback.base import BaseHandler as CallbackHandler
from extensions.handlers.message.base import BaseHandler as MessageHandler
from extensions.handlers.message.use_timezone_extension import (
    UseTimeZoneHandlerExtension,
)
from middlewares.data import MiddlewareData, UserData, require_user_data
from middlewares.user_data import UserDataMiddleware


class ConcreteMessageHandler(MessageHandler):
    async def handle(self) -> None:
        pass


class ConcreteCallbackHandler(CallbackHandler):
    async def handle(self) -> None:
        pass


class TimezoneHandler(UseTimeZoneHandlerExtension):
    async def handle(self) -> None:
        pass


async def test_user_context_is_shared_between_messages_and_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(UserDataMiddleware, "_UserDataMiddleware__data", {})
    handler = AsyncMock(return_value="handled")
    message = MagicMock(spec=Message, from_user=MagicMock(id=7))
    callback = MagicMock(spec=CallbackQuery, from_user=MagicMock(id=7))
    other_user = MagicMock(spec=Message, from_user=MagicMock(id=8))
    message_data: MiddlewareData = {}
    callback_data: MiddlewareData = {}
    other_data: MiddlewareData = {}

    assert await UserDataMiddleware()(handler, message, message_data) == "handled"
    user_data = require_user_data(message_data)
    assert user_data == {"delete_queue": []}
    user_data["tz"] = timedelta(hours=3)
    await UserDataMiddleware()(handler, callback, callback_data)
    await UserDataMiddleware()(handler, other_user, other_data)

    assert require_user_data(callback_data) is user_data
    assert require_user_data(callback_data).get("tz") == timedelta(hours=3)
    assert require_user_data(other_data) == {"delete_queue": []}
    assert (
        require_user_data(other_data)["delete_queue"] is not user_data["delete_queue"]
    )


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
