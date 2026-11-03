from typing import Any

from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from ui.keyboards.reminder import RemindMarkup
from ._base import BaseHandler
from ._states import FSM


class TextInputHandler(BaseHandler, OneTimeMessageHandlerExtension):
    async def handle(self) -> Any:
        await self.event.delete()
        await self.state.set_state(FSM.get_date)
        self.set(self.props.text, self.event.text)
        await self.render_widget()
        self._set_one_time_message(
            (await self.event.answer("Введите дату", reply_markup=RemindMarkup.date))
        )
