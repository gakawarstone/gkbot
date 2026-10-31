from aiogram.types import Message

from .base import BaseHandler


class OneTimeMessageHandlerExtension(BaseHandler):
    def _set_one_time_message(self, message: Message) -> None:
        self.user_data["delete_queue"].append(message)
