from aiogram.filters import BaseFilter
from aiogram.types import Message


class LongMessageFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return len(message.text) > 200
