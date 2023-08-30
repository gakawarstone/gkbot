import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


class YouTubeVideoLink(BaseFilter):
    __pattern = (r'http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?'
                 r'v=|\.be\/)([\w\-\_]*)(&(amp;)?[\w\?=]*)?')

    async def __call__(self, telegram_object: Message):
        if not isinstance(telegram_object, Message):
            return False
        if not telegram_object.text:
            return False
        return re.search(self.__pattern, telegram_object.text)
