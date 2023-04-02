from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from aiogram.types import CallbackQuery, User, Message, Chat

fake_event = AsyncMock()


def make_fake_message(text: str) -> Message:
    return Message(
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
        data=data
    )  # type: ignore
