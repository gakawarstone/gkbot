from aiogram import flags

from .base import BaseHandler


# NOTE: added to silence linter
#       because aiogram flags is not typed correctly
@flags.require_timezone
class UseTimeZoneHandlerExtension(BaseHandler):  # type: ignore[misc]
    @property
    def tz(self):
        return self.user_data["tz"]
