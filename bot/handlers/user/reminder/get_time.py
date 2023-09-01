from datetime import time
from typing import Any

from contrib.handlers.message.one_time_extension import \
    OneTimeMessageHandlerExtension
from ._base import BaseHandler
from ._exceptions import InvalidTimeInput
from ._states import FSM
from .create import CreateRemindHandler


class TimeInputHandler(BaseHandler, OneTimeMessageHandlerExtension):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        try:
            _time = self._validate_time(self.event.text)
            self.set(self.props.time, _time)
            await CreateRemindHandler(self.event, data=self.user_data).handle()
        except InvalidTimeInput:
            await self.state.set_state(FSM.get_time)
            await self.render_widget(status_message=self.status.invalid_time)
            self._set_one_time_message((
                await self.event.answer('Введите время')
            ))

    def _validate_time(self, _time: str) -> time:
        try:
            return time(*map(int, _time.split(':')))
        except ValueError:
            raise InvalidTimeInput
