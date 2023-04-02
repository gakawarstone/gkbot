from unittest.mock import AsyncMock
from datetime import datetime
from typing import Any

from aiogram.types import CallbackQuery, User, Message, Chat

fake_event = AsyncMock()


class MockedMessage(Message):
    async def answer(*args: Any, **kwargs: Any) -> Any:
        pass

    async def delete(*args: Any) -> Any:
        pass


def make_fake_message(text: str) -> Message:
    return MockedMessage(
        message_id=42,
        date=datetime.now(),
        text=text,
        chat=Chat(id=42, type="private"),
        from_user=User(id=1, is_bot=False, first_name="Test"),
    )  # type: ignore


def make_fake_callback(data: str) -> CallbackQuery:
    return CallbackQuery(
        from_user=User(id=1, is_bot=False, first_name='user'),
        id=1,
        chat_instance='1',
        data=data,
        message=make_fake_message('mock')
    )  # type: ignore
