"""Shared contracts for aiogram injection and the per-user conversation cache."""

from collections.abc import Awaitable, Callable
from datetime import date as Date
from datetime import time as Time
from datetime import timedelta
from typing import Any, Protocol, Required, TypedDict

from aiogram.dispatcher.middlewares.data import MiddlewareData as AiogramMiddlewareData
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject


class RestartableHandler(Protocol):
    @property
    def user_data(self) -> "UserData": ...

    @property
    def event(self) -> Message: ...

    @property
    def state(self) -> FSMContext: ...

    async def handle(self) -> object: ...


class UserData(TypedDict, total=False):
    """Values retained between updates for one Telegram user.

    The queue exists as soon as UserDataMiddleware has run. Other fields are
    populated by a flagged middleware or a conversation step, and may be absent.
    Legacy context-manager fields can also be reset to None.
    """

    delete_queue: Required[list[Message]]
    tz: timedelta | None
    callback: RestartableHandler
    habit_name: str | None
    habit_notify_time: Time
    messages: list[str] | None
    file_name: str | None
    text: str | None
    date: Date | None
    time: Time | None
    message: Message | None
    name: str | None
    author: str | None
    chapter_cnt: int | None
    property_name: str | None
    new_value: str | None
    book_id: int | None
    setting_name: str | None
    setting_new_value: Time | None


class MiddlewareData(AiogramMiddlewareData, total=False):
    """Aiogram context, including project values at their injection stages."""

    data: UserData
    admins: list[int]


# Aiogram intentionally allows arbitrary downstream return values.
MiddlewareHandler = Callable[[TelegramObject, MiddlewareData], Awaitable[Any]]


def require_user_data(data: MiddlewareData) -> UserData:
    """Require the value installed by UserDataMiddleware on messages/callbacks."""
    user_data = data.get("data")
    if user_data is None:
        raise RuntimeError("UserDataMiddleware must run before accessing user data")
    return user_data
