from aiogram.dispatcher.filters import BaseFilter
from aiogram.types import Message


class TikTokVideoLink(BaseFilter):
    patterns = (
        'https://vm.tiktok.com/',
        'https://vr.tiktok.com/',
        'https://www.tiktok.com/'
    )

    async def __call__(self, message: Message):
        return message.text.startswith(self.patterns)
