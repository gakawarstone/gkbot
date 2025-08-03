from aiogram.filters import BaseFilter
from aiogram.types import Message

from core.types import ChatType


class ChatTypeFilter(BaseFilter):
    # TODO: allowed: list[ChatType]
    def __init__(self, chat_type: ChatType | list[ChatType]) -> None:
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        m_type = ChatType(message.chat.type)

        if isinstance(self.chat_type, ChatType):
            return m_type == self.chat_type

        allowed: list[ChatType] = list(self.chat_type)
        return m_type in allowed
