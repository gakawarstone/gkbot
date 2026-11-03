from typing import Any

from ._base import BaseHandler
from ._states import AddBookFSM as FSM


class GetNameHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_author)
        await self.event.delete()
        self.set(self.props.name, self.event.text)
        await self.render_widget()
