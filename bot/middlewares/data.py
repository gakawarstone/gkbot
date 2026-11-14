"""Shared contracts for aiogram injection and the per-user conversation cache."""

from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any, Required, TypedDict

from aiogram.dispatcher.middlewares.data import MiddlewareData as AiogramMiddlewareData
from aiogram.fsm.state import State
from aiogram.types import Message, TelegramObject


class UserData(TypedDict, total=False):
    """Values retained between updates for one Telegram user.

    The queue exists as soon as UserDataMiddleware has run. Other fields are
    populated by timezone or confirmation handlers and may be absent.
    """

    delete_queue: Required[list[Message]]
    tz: timedelta | None
    confirmation: tuple[
        Callable[[], Awaitable[Any]], Callable[[], Awaitable[Any]] | None, State
    ]


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
