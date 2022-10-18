from aiogram.filters import BaseFilter
from aiogram.types import Message, InlineQuery


class TikTokVideoLink(BaseFilter):
    patterns = (
        'https://vm.tiktok.com/',
        'https://vr.tiktok.com/',
        'https://www.tiktok.com/'
    )

    async def __call__(self, telegram_object: Message | InlineQuery):
        if type(telegram_object) == Message:
            return telegram_object.text.startswith(self.patterns)  # BUG
        return telegram_object.query.startswith(self.patterns)
