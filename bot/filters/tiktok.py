import re

from aiogram.filters import BaseFilter
from aiogram.types import Message, InlineQuery


class TikTokVideoLink(BaseFilter):
    pattern = re.compile(r"https://(www|vm|vr|vt).tiktok.com/")

    async def __call__(self, telegram_object: Message | InlineQuery) -> bool:
        if isinstance(telegram_object, Message):
            text = telegram_object.text or ""
            return bool(self.pattern.search(text))
        query = telegram_object.query or ""
        return bool(self.pattern.search(query))
