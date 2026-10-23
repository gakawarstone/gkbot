from datetime import UTC, datetime

import pytest
from aiogram.enums import ChatType
from aiogram.types import Chat, Message

from filters.chat_type import ChatTypeFilter


@pytest.mark.parametrize("message_type", list(ChatType))
@pytest.mark.parametrize(
    "allowed", [ChatType.PRIVATE, [ChatType.GROUP, ChatType.SUPERGROUP], []]
)
async def test_chat_type_filter(
    message_type: ChatType, allowed: ChatType | list[ChatType]
) -> None:
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=1, type=message_type),
    )
    expected = [allowed] if isinstance(allowed, ChatType) else allowed

    assert await ChatTypeFilter(allowed)(message) == (message_type in expected)
