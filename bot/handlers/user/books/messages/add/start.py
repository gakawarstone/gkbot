from typing import Any

from ui.components.book_creator import BookCreatorComponent
from ._base import BaseHandler
from ._states import AddBookFSM as FSM


class InitAddBookHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_name)
        await self.event.delete()
        self.clean_context()
        text = BookCreatorComponent().render()
        self.set(self.props.message, (await self.event.answer(text)))
