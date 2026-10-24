import socket
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import NoReturn
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot import handlers, middlewares, modules
from bot.middlewares.user_data import UserDataMiddleware
from models.users import Users
from services.timezone import TimeZone
from tests.dispatcher.helpers import (
    ADMIN_IDS,
    DispatcherHarness,
    ObserveInvocation,
    RecordingSession,
)


def deny_network(*args: object, **kwargs: object) -> NoReturn:
    # BaseException-based pytest failure bypasses the registered error handler.
    pytest.fail("Dispatcher tests must not open network connections or resolve hosts")


@pytest.fixture
async def dispatcher_harness(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[DispatcherHarness]:
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)
    monkeypatch.setattr(socket, "getaddrinfo", deny_network)
    monkeypatch.setattr(UserDataMiddleware, "_UserDataMiddleware__data", {})

    find_user = AsyncMock(return_value=None)
    create_user = AsyncMock()
    monkeypatch.setattr(
        Users, "filter", MagicMock(return_value=MagicMock(first=find_user))
    )
    monkeypatch.setattr(Users, "create", create_user)
    get_timezone = AsyncMock(return_value=timedelta(hours=3))
    set_timezone = AsyncMock()
    monkeypatch.setattr(TimeZone, "get_user_timezone", get_timezone)
    monkeypatch.setattr(TimeZone, "set_user_timezone", set_timezone)

    session = RecordingSession()
    bot = Bot(token="12345678:ABCDEF-GHIJKLMNOPQRSTUV", session=session)
    dispatcher = Dispatcher(storage=MemoryStorage(), admins=ADMIN_IDS)
    middlewares.setup(dispatcher)
    handlers.setup(dispatcher)
    modules.setup(dispatcher)
    harness = DispatcherHarness(
        dispatcher, bot, session, find_user, create_user, get_timezone, set_timezone
    )
    observer = ObserveInvocation(harness.invocations)
    for event in (
        dispatcher.message,
        dispatcher.callback_query,
        dispatcher.inline_query,
    ):
        event.middleware(observer)
    try:
        yield harness
    finally:
        await dispatcher.fsm.close()
        await session.close()
