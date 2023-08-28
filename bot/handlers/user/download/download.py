from typing import Any

from aiogram.types import BufferedInputFile

from services.http import HttpService
from ._base import BaseHandler
from ._states import FSM


class DownloadHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        content = await HttpService.get(self.event.text)
        file = BufferedInputFile(content, self.ctx.file_name)
        await self.event.answer_document(file)
