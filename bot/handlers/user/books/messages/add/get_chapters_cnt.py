from typing import Any

from ._base import BaseHandler
from ._states import AddBookFSM as FSM
from .create import CreateBookHandler


class GetChaptersCnt(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        self.set(self.props.chapter_cnt, int(self.event.text))
        await self.render_widget()
        await CreateBookHandler(
            self.event, state=self.state, data=self.user_data
        ).handle()
