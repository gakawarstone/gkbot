from aiogram.filters import BaseFilter
from aiogram.types import Message
from pydantic_core.core_schema import model_ser_schema


class LongMessageFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text.startswith("/"):
            return False
        if not message.text:
            return False
        return len(message.text) > 200
