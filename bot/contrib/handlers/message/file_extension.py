from io import BytesIO

from .base import BaseHandler

from settings import API_SERVER_URL


class NoFileException(Exception):
    """No document sended"""


class FileHandlerExtension(BaseHandler):
    @property
    async def document_io(self) -> BytesIO:
        if not self.event.document:
            raise NoFileException

        if API_SERVER_URL == 'https://api.telegram.org':
            file = await self.state.bot.get_file(self.event.document.file_id)
            file_path = file.file_path
        else:
            file_path = self.event.document.file_id

        file_io = BytesIO()
        await self.state.bot.download_file(file_path, file_io)
        return file_io
