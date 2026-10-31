from datetime import UTC, datetime

from aiogram.enums import ChatType
from aiogram.types import Chat, Message

from filters.chat_type import ChatTypeFilter


async def test_chat_type_filter_rejects_channel_without_raising() -> None:
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=1, type=ChatType.CHANNEL),
    )

    assert await ChatTypeFilter(ChatType.PRIVATE)(message) is False
