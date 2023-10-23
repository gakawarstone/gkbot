from datetime import date, datetime, timedelta
from typing import Any

from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from ._base import BaseHandler
from ._exceptions import InvalidDateInput
from ._states import FSM
from ui.keyboards.reminder import RemindMarkup


class DateInputHandler(BaseHandler, OneTimeMessageHandlerExtension):
    async def handle(self) -> Any:
        await self.event.delete()
        try:
            await self.state.set_state(FSM.get_time)
            _date = self._validate_input(self.event.text)
            self.set(self.props.date, _date)
            await self.render_widget()
            self._set_one_time_message((await self.event.answer("Введите время")))
        except InvalidDateInput:
            await self.state.set_state(FSM.get_date)
            await self.render_widget(status_message=self.status.invalid_date)
            self._set_one_time_message(
                (
                    await self.event.answer(
                        "Введите дату", reply_markup=RemindMarkup.date
                    )
                )
            )

    def _validate_input(self, text: str) -> datetime:
        match text:  # [ ] move to contrib and datemarkup
            case RemindMarkup.buttons.today | "1":
                return date.today()
            case RemindMarkup.buttons.tomorrow | "2":
                return date.today() + timedelta(days=1)
            case _:
                return self._validate_date(text)

    def _validate_date(self, text: str, __format: str = "%d.%m.%Y") -> datetime:
        try:
            return datetime.strptime(text, __format).date()
        except ValueError:
            raise InvalidDateInput
