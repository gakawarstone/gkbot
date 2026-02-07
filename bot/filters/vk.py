import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


class VkVideoLink(BaseFilter):
    __pattern = (
        r"https://(vk\.com|vkvideo\.ru)/(wall-\d+|video-\d+_\d+)"
        r"|https://vk\.cc/[\w-]+"
    )

    async def __call__(self, telegram_object: Message) -> bool:
        if not isinstance(telegram_object, Message):
            return False
        text = telegram_object.text or ""
        return bool(re.search(self.__pattern, text))
