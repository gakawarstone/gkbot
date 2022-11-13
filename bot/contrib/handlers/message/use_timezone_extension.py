from .base import BaseHandler

from aiogram import flags


@flags.require_timezone
class UseTimeZoneHandlerExtension(BaseHandler):
    @property
    def tz(self):
        return self.user_data['tz']
