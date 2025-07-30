from aiogram.filters import BaseFilter
from aiogram.types import Message

from configs.admins import ADMINS


class BotAdmin(BaseFilter):
    admins = ADMINS

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False

        return message.from_user.id in self.admins
