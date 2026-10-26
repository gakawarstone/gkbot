from aiogram.filters import BaseFilter
from aiogram.types import Message


class BotAdmin(BaseFilter):
    async def __call__(self, message: Message, admins: list[int]) -> bool:
        if message.from_user is None:
            return False

        return message.from_user.id in admins
