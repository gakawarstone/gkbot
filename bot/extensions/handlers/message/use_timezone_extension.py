from .base import BaseHandler

from aiogram import flags


# NOTE: added to silence linter
#       because aiogram flags is not typed correctly
@flags.require_timezone
class UseTimeZoneHandlerExtension(BaseHandler):  # type: ignore[misc]
    @property
    def tz(self):
        return self.user_data["tz"]
