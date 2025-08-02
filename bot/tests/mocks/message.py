from unittest.mock import AsyncMock
import datetime
from typing import Any

from aiogram.types import CallbackQuery, User, Message, Chat

fake_event = AsyncMock()


class MockedMessage(Message):
    async def answer(*args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        return MockedMessage(
            message_id=42,
            date=datetime.datetime.now(),
            text=args[1],
            chat=Chat(id=42, type="private"),
            from_user=User(id=1, is_bot=False, first_name="Test"),  # pyright: ignore[reportCallIssue]
        )  # type: ignore  # pyright: ignore[reportCallIssue]

    async def delete(*args: Any) -> Any:  # type: ignore[override]
        pass


def make_fake_message(text: str) -> Message:
    return MockedMessage(
        message_id=42,
        date=datetime.datetime.now(),
        text=text,
        chat=Chat(id=42, type="private"),
        from_user=User(id=1, is_bot=False, first_name="Test"),  # pyright: ignore[reportCallIssue]
    )  # type: ignore  # pyright: ignore[reportCallIssue]


def make_fake_callback(data: str) -> CallbackQuery:
    return CallbackQuery(
        from_user=User(id=1, is_bot=False, first_name="user"),
        id="1",
        chat_instance="1",
        data=data,
        message=make_fake_message("mock"),
    )  # type: ignore
