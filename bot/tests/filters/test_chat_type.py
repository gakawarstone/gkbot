from datetime import datetime

from aiogram.enums import ChatType
from aiogram.types import Chat, Message

from filters.chat_type import ChatTypeFilter


async def test_channel_is_rejected_by_chat_type_filter() -> None:
    message = Message(message_id=1, date=datetime.now(), chat=Chat(id=1, type="channel"))

    assert not await ChatTypeFilter(ChatType.PRIVATE)(message)
    assert not await ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP])(message)
