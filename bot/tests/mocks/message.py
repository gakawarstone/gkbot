from datetime import datetime

from aiogram.types import Message, Chat, User

fake_message = Message(
    message_id=42,
    date=datetime.now(),
    text="test",
    chat=Chat(id=42, type="private"),
    from_user=User(id=42, is_bot=False, first_name="Test"),
)
