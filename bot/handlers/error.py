import traceback
from typing import Any, cast
from datetime import datetime

from aiogram import Router
from aiogram.types import BufferedInputFile
from aiogram.handlers import ErrorHandler as _BaseHandler
from aiogram.types.error_event import ErrorEvent


class ErrorHandler(_BaseHandler):
    def __init__(self, event: Exception, admins: list[int], **data: Any) -> None:
        super().__init__(event, **data)
        self._admins = admins

    async def handle(self) -> Any:
        for admin in self._admins:
            await self.bot.send_document(
                chat_id=admin, document=self._traceback_file, caption=self._caption
            )

    @property
    def _traceback_file(self) -> BufferedInputFile:
        tb = self._error_event.exception.__traceback__
        tb_str = "".join(traceback.format_tb(tb))
        file_content = bytes(tb_str, "utf-8")
        return BufferedInputFile(file_content, "traceback.txt")

    @property
    def _caption(self) -> str:
        text = "Error: " + str(self._error_event.exception) + "\n"
        text += "User: @" + self._try_get_username() + "\n"
        text += "Date: " + str(datetime.now().astimezone()) + "\n"
        return text

    def _try_get_username(self) -> str:
        if not self._error_event.update.message:
            return ""
        if not self._error_event.update.message.from_user:
            return ""
        if not self._error_event.update.message.from_user.username:
            return ""
        return self._error_event.update.message.from_user.username

    @property
    def _error_event(self) -> ErrorEvent:
        return cast(ErrorEvent, self.event)


def setup(r: Router):
    r.error.register(ErrorHandler)
