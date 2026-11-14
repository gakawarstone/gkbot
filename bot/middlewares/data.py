"""Shared contracts for aiogram injection and the per-user conversation cache."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.dispatcher.middlewares.data import MiddlewareData as AiogramMiddlewareData
from aiogram.types import TelegramObject


class MiddlewareData(AiogramMiddlewareData, total=False):
    """Aiogram context, including project values at their injection stages."""

    data: dict[str, Any]
    admins: list[int]


# Aiogram intentionally allows arbitrary downstream return values.
MiddlewareHandler = Callable[[TelegramObject, MiddlewareData], Awaitable[Any]]


def require_user_data(data: MiddlewareData) -> dict[str, Any]:
    """Require the value installed by UserDataMiddleware on messages/callbacks."""
    user_data = data.get("data")
    if user_data is None:
        raise RuntimeError("UserDataMiddleware must run before accessing user data")
    return user_data
