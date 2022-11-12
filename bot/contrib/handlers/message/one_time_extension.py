from .base import BaseHandler

from aiogram.types import Message


class OneTimeMessageHandlerExtension(BaseHandler):
    def _set_one_time_message(self, message: Message):
        self.user_data['delete_queue'].append(message)
