from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

from extensions.handlers.message.base import BaseHandler
from services.http import HttpService
from configs.commands import USER_COMMANDS


class DownloadAsura(BaseHandler):
    _headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.3"
        ),
        "Host": "ranobe.me",
        "Referer": "https://ranobe.me/ranobe24",
    }
    _url = "https://ranobe.me/section_fictofile_download.php?id=24&format=fb2"

    async def handle(self) -> Any:
        await self.event.delete()
        file = await HttpService.get(self._url, headers=self._headers)
        await self.bot.send_document(
            chat_id=self.event.chat.id, document=BufferedInputFile(file, "asura.zip")
        )


def setup(r: Router):
    r.message.register(DownloadAsura, Command(USER_COMMANDS.get_asura))
