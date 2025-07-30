from aiogram.filters import BaseFilter
from aiogram.types import Message


class NotCommandFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text is None:
            return False

        return not message.text.startswith("/")
