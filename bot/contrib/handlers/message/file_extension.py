from io import BytesIO

from .base import BaseHandler


class NoFileException(Exception):
    """No document sended"""


class FileHandlerExtension(BaseHandler):
    @property
    async def document_io(self) -> BytesIO:
        if not self.event.document:
            raise NoFileException

        file = await self.state.bot.get_file(self.event.document.file_id)
        file_path = file.file_path
        file_io = BytesIO()
        await self.state.bot.download_file(file_path, file_io)
        return file_io
