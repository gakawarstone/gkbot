from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import Message


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: ChatType | list[ChatType]) -> None:
        self.allowed = frozenset(
            [chat_type] if isinstance(chat_type, ChatType) else chat_type
        )

    async def __call__(self, message: Message) -> bool:
        return message.chat.type in self.allowed
