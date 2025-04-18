import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


class VkVideoLink(BaseFilter):
    __pattern = r"https://vk\.com/(wall-\d+|video-\d+_\d+)|https://vk\.cc/[\w-]+"

    async def __call__(self, telegram_object: Message):
        if not isinstance(telegram_object, Message):
            return False
        if not telegram_object.text:
            return False
        return re.search(self.__pattern, telegram_object.text)
