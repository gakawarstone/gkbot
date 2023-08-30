from typing import Any

from aiogram import Router
from aiogram.handlers import ErrorHandler as _BaseHandler

from lib.notifier import Notifier
from settings import ADMINS


class ErrorHandler(_BaseHandler):
    async def handle(self) -> Any:
        text = self.exception_name + self.exception_message
        [await Notifier.notify(admin, text) for admin in ADMINS]


def setup(r: Router):
    r.error.register(ErrorHandler)
