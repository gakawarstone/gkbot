import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


class YouTubeVideoLink(BaseFilter):
    __pattern = (r'http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?'
                 r'v=|\.be\/)([\w\-\_]*)(&(amp;)?[\w\?=]*)?')

    async def __call__(self, telegram_object: Message) -> bool:
        if not isinstance(telegram_object, Message):
            return False
        text = telegram_object.text or ""
        return bool(re.search(self.__pattern, text))
