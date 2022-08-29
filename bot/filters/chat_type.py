from aiogram.filters import BaseFilter
from aiogram.types import Message

from lib.types import ChatType


class ChatTypeFilter(BaseFilter):
    chat_type: ChatType | list[ChatType]

    async def __call__(self, message: Message) -> bool:
        if type(self.chat_type) == ChatType:
            return ChatType(message.chat.type) == self.chat_type
        else:
            return ChatType(message.chat.type) in self.chat_type
