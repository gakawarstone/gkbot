from aiogram.filters import BaseFilter
from aiogram.types import Message


class LongMessageFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if not hasattr(message, "text") or not message.text:
            return False
        if message.text.startswith("/"):
            return False
        if not message.text:
            return False
        return len(message.text) > 200
