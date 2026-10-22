from typing import Any

from aiogram.types import FSInputFile

from services.http import HttpService

from ._base import BaseHandler
from ._states import FSM


class DownloadHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        async with HttpService.download_file(self.event.text) as file_path:
            file = FSInputFile(file_path, self.ctx.file_name)
            await self.event.answer_document(file)
