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

        file = await self.state.bot.get_file(self.event.document.file_id)
        file_path = file.file_path

        if API_SERVER_URL == 'https://api.telegram.org':
            file_io = BytesIO()
            await self.state.bot.download_file(file_path, file_io)
        else:
            file_io = BytesIO(open(file_path, 'rb').read())

        return file_io
