from typing import Any

from ui.components.remind_creator import RemindCreator
from ._states import FSM
from ._base import BaseHandler

# [ ] require tz


class InitHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_text)
        await self.event.delete()
        self.clean_context()
        text = RemindCreator().render()
        self.set(self.props.message, (await self.event.answer(text)))
