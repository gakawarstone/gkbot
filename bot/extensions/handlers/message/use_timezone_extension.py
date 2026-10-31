from datetime import timedelta
from typing import ClassVar

from .base import BaseHandler


class UseTimeZoneHandlerExtension(BaseHandler):
    # FlagDecorator erases the class type. Aiogram reads this same attribute.
    aiogram_flag: ClassVar[dict[str, bool]] = {"require_timezone": True}

    @property
    def tz(self) -> timedelta:
        tz = self.user_data.get("tz")
        if tz is None:
            raise RuntimeError("This handler requires a timezone")
        return tz
