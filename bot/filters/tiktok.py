import re

from aiogram.filters import BaseFilter
from aiogram.types import Message, InlineQuery


class TikTokVideoLink(BaseFilter):
    pattern = re.compile(r'https://(www|vm|vr).tiktok.com/')

    async def __call__(self, telegram_object: Message | InlineQuery):
        if isinstance(telegram_object, Message):
            return self.pattern.match(telegram_object.text)
        return self.pattern.match(telegram_object.query)
