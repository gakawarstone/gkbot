from typing import Any

from ._base import BaseHandler
from ._states import AddBookFSM as FSM


class GetAuthorHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_chapters_cnt)
        await self.event.delete()
        self.set(self.props.author, self.event.text)
        await self.render_widget()
