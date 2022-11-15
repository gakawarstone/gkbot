from typing import Any

from ._base import BaseHandler
from ._states import AddBookFSM as FSM
from .create import CreateBookHandler


class GetChaptersCnt(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        self.set(self.props.chapter_cnt, int(self.event.text))
        await CreateBookHandler(self.event, state=self.state,
                                data=self.user_data).handle()
