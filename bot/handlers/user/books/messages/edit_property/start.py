from typing import Any

from ._base import BaseHandler
from ._states import FSM


class InitEditBookPropertyHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_new_value)
        # self.clean_context(
        #     self.props.book_id, self.props.property_name) # BUG:
        text = f'Введите новое значение для {self.ctx.property_name}'
        await self.event.answer(text)
