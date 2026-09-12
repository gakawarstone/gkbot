from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from middlewares.delete_queue import DeleteQueueMiddleware
from middlewares.not_enough_rights import NotEnoughRightsMiddleware
from middlewares.register_user import RegisterUserMiddleware
from middlewares.timezone import TimeZoneMiddleware
from middlewares.user_data import UserDataMiddleware
from services.timezone import UserDontHaveTimeZone


def make_event(user_id: int = 1) -> MagicMock:
    event = MagicMock()
    event.from_user.id = user_id
    event.from_user.full_name = "Test User"
    return event


def make_message_event(user_id: int = 1) -> MagicMock:
    event = MagicMock()
    event.__class__ = Message
    event.from_user.id = user_id
    event.answer = AsyncMock()
    return event


@pytest.fixture(autouse=True)
def _clear_user_data() -> Any:
    UserDataMiddleware._UserDataMiddleware__data.clear()  # type: ignore[attr-defined]
    yield
    UserDataMiddleware._UserDataMiddleware__data.clear()  # type: ignore[attr-defined]


async def test_register_user_returns_downstream_result() -> None:
    middleware = RegisterUserMiddleware()
    handler = AsyncMock(return_value="ok")
    event = make_event()

    with (
        patch("middlewares.register_user.Users.filter") as mock_filter,
        patch("middlewares.register_user.Users.create") as mock_create,
    ):
        mock_filter.return_value.first = AsyncMock(return_value=MagicMock())
        result = await middleware(handler, event, {})

    assert result == "ok"
    handler.assert_awaited_once()
    mock_create.assert_not_awaited()


async def test_register_user_creates_missing_user_and_returns_result() -> None:
    middleware = RegisterUserMiddleware()
    handler = AsyncMock(return_value="ok")
    event = make_event()

    with (
        patch("middlewares.register_user.Users.filter") as mock_filter,
        patch("middlewares.register_user.Users.create") as mock_create,
    ):
        mock_filter.return_value.first = AsyncMock(return_value=None)
        mock_create.return_value = AsyncMock()
        result = await middleware(handler, event, {})

    assert result == "ok"
    mock_create.assert_awaited_once()


async def test_user_data_returns_downstream_result() -> None:
    middleware = UserDataMiddleware()
    handler = AsyncMock(return_value="ok")

    result = await middleware(handler, make_event(7), {})

    assert result == "ok"
    handler.assert_awaited_once()


async def test_delete_queue_returns_downstream_result() -> None:
    middleware = DeleteQueueMiddleware()
    handler = AsyncMock(return_value="ok")

    result = await middleware(handler, MagicMock(), {"data": {"delete_queue": []}})

    assert result == "ok"
    handler.assert_awaited_once()


async def test_timezone_non_message_returns_downstream_result() -> None:
    middleware = TimeZoneMiddleware()
    handler = AsyncMock(return_value="ok")

    result = await middleware(handler, MagicMock(), {"data": {}})

    assert result == "ok"
    handler.assert_awaited_once()


async def test_timezone_without_flag_returns_downstream_result() -> None:
    middleware = TimeZoneMiddleware()
    handler = AsyncMock(return_value="ok")
    event = make_message_event()

    with patch("middlewares.timezone.get_flag", return_value=None):
        result = await middleware(handler, event, {"data": {}})

    assert result == "ok"
    handler.assert_awaited_once()


async def test_timezone_with_tz_returns_downstream_result() -> None:
    middleware = TimeZoneMiddleware()
    handler = AsyncMock(return_value="ok")
    event = make_message_event()
    data: dict[str, Any] = {"data": {}}

    with (
        patch("middlewares.timezone.get_flag", return_value=True),
        patch(
            "middlewares.timezone.TimeZone.get_user_timezone",
            return_value=timedelta(hours=3),
        ),
    ):
        result = await middleware(handler, event, data)

    assert result == "ok"
    assert data["data"]["tz"] == timedelta(hours=3)
    handler.assert_awaited_once()


async def test_timezone_short_circuit_returns_none() -> None:
    middleware = TimeZoneMiddleware()
    handler = AsyncMock(return_value="ok")
    event = make_message_event()

    with (
        patch("middlewares.timezone.get_flag", return_value=True),
        patch(
            "middlewares.timezone.TimeZone.get_user_timezone",
            side_effect=UserDontHaveTimeZone,
        ),
    ):
        result = await middleware(handler, event, {"data": {}})

    assert result is None
    handler.assert_not_awaited()
    event.answer.assert_awaited_once()


async def test_not_enough_rights_returns_downstream_result() -> None:
    middleware = NotEnoughRightsMiddleware()
    handler = AsyncMock(return_value="ok")

    result = await middleware(handler, MagicMock(), {})

    assert result == "ok"
    handler.assert_awaited_once()


async def test_not_enough_rights_short_circuit_returns_none() -> None:
    middleware = NotEnoughRightsMiddleware()
    event = make_message_event()
    error = TelegramBadRequest(
        method=MagicMock(), message="Bad Request: message can't be deleted"
    )
    handler = AsyncMock(side_effect=error)

    result = await middleware(handler, event, {})

    assert result is None
    event.answer.assert_awaited_once()


async def test_not_enough_rights_reraises_unexpected_error() -> None:
    middleware = NotEnoughRightsMiddleware()
    error = TelegramBadRequest(method=MagicMock(), message="Bad Request: other")
    handler = AsyncMock(side_effect=error)

    with pytest.raises(TelegramBadRequest):
        await middleware(handler, MagicMock(), {})
