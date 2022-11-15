from typing import Any

from ._base import BaseHandler
from ._states import AddBookFSM as FSM


class InitAddBookHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_name)
        await self.event.answer('Вы пытаетесь добавить книгу. Введите название')
        self.clean_context()
