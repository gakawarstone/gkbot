import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


class VkVideoLink(BaseFilter):
    __pattern = r'https:\/\/vk\.com\/video(-?\d+)_(\d+)'

    async def __call__(self, telegram_object: Message):
        return re.search(self.__pattern, telegram_object.text)
