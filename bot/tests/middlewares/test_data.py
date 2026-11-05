from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message

from extensions.handlers.message.base import BaseHandler as MessageHandler
from extensions.handlers.message.use_timezone_extension import (
    UseTimeZoneHandlerExtension,
)
from middlewares.data import MiddlewareData, UserData, require_user_data
from middlewares.user_data import UserDataMiddleware


class ConcreteMessageHandler(MessageHandler):
    async def handle(self) -> None:
        pass


class TimezoneHandler(UseTimeZoneHandlerExtension):
    async def handle(self) -> None:
        pass


async def test_user_context_is_shared_between_messages_and_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(UserDataMiddleware, "_UserDataMiddleware__data", {})
    handler = AsyncMock()
    middleware = UserDataMiddleware()
    message = MagicMock(spec=Message, from_user=MagicMock(id=7))
    callback = MagicMock(spec=CallbackQuery, from_user=MagicMock(id=7))
    other_user = MagicMock(spec=Message, from_user=MagicMock(id=8))
    message_data: MiddlewareData = {}
    callback_data: MiddlewareData = {}
    other_data: MiddlewareData = {}

    await middleware(handler, message, message_data)
    user_data = require_user_data(message_data)
    user_data["tz"] = timedelta(hours=3)
    await middleware(handler, callback, callback_data)
    await middleware(handler, other_user, other_data)

    assert require_user_data(callback_data).get("tz") == timedelta(hours=3)
    assert require_user_data(other_data).get("tz") is None


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
