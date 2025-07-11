from io import BytesIO

from configs.api_server import API_SERVER_URL, BOT_API_DIR
from .base import BaseHandler


class NoFileException(Exception):
    """No document sent"""


class FileHandlerExtension(BaseHandler):
    async def _get_io(self, file_id: str) -> BytesIO:
        file = await self.bot.get_file(file_id)
        file_path = file.file_path

        if file_path is None:
            raise ValueError("File path cannot be None")

        if API_SERVER_URL == "https://api.telegram.org":
            file_io = BytesIO()
            await self.bot.download_file(file_path, file_io)
        else:
            bot_token = self.bot.token
            file_path = f"{BOT_API_DIR}/{bot_token}/{file_path}"
            file_io = BytesIO(open(file_path, "rb").read())

        return file_io

    @property
    async def document_io(self) -> BytesIO:
        if not self.event.document:
            raise NoFileException
        return await self._get_io(self.event.document.file_id)

    @property
    async def photo_io(self) -> BytesIO:
        if not self.event.photo:
            raise NoFileException
        return await self._get_io(self.event.photo[-1].file_id)
