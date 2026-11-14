from datetime import timedelta
from typing import Any, cast

from aiogram import flags

from .base import BaseHandler


# Aiogram types this class decorator as a generic callable.
@cast(Any, flags.require_timezone)
class UseTimeZoneHandlerExtension(BaseHandler):
    @property
    def tz(self) -> timedelta:
        tz = self.user_data.get("tz")
        if tz is None:
            raise RuntimeError("This handler requires a timezone")
        return tz
