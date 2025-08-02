import traceback
from typing import Any
from datetime import datetime

from aiogram import Router
from aiogram.types import BufferedInputFile
from aiogram.handlers import ErrorHandler as _BaseHandler
from aiogram.types.error_event import ErrorEvent

from configs.admins import ADMINS


class ErrorHandler(_BaseHandler):
    event: ErrorEvent

    async def handle(self) -> Any:
        [
            await self.bot.send_document(
                chat_id=admin, document=self._traceback_file, caption=self._caption
            )
            for admin in ADMINS
        ]

    @property
    def _traceback_file(self) -> BufferedInputFile:
        tb = self.event.exception.__traceback__
        tb_str = "".join(traceback.format_tb(tb))
        file_content = bytes(tb_str, "utf-8")
        return BufferedInputFile(file_content, "traceback.txt")

    @property
    def _caption(self) -> str:
        text = "Error: " + str(self.event.exception) + "\n"
        text += "User: @" + self._try_get_username() + "\n"
        text += "Date: " + str(datetime.now()) + "\n"
        return text

    def _try_get_username(self) -> str:
        try:
            return self.event.update.message.from_user.username
        except AttributeError:
            return ""


def setup(r: Router):
    r.error.register(ErrorHandler)
