from aiogram.filters import BaseFilter
from aiogram.types import Message

from core.types import ChatType


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: ChatType | list[ChatType]) -> None:
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if type(self.chat_type) is ChatType:
            return ChatType(message.chat.type) == self.chat_type
        else:
            return ChatType(message.chat.type) in self.chat_type
