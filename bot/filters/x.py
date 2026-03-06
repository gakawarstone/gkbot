import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


class XVideoLink(BaseFilter):
    # Matches x.com, twitter.com, mobile.x.com, mobile.twitter.com, etc.
    # Matches /i/status/ID and /username/status/ID
    __pattern = (
        r"https?://(?:[a-z0-9]+\.)?(?:x|twitter)\.com/"
        r"(?:i/status/|[A-Za-z0-9_]+/status/)\d+"
    )

    async def __call__(self, telegram_object: Message) -> bool:
        text = telegram_object.text or ""
        return bool(re.search(self.__pattern, text))
