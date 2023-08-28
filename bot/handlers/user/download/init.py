from typing import Any

from contrib.handlers.message.one_time_extension import \
    OneTimeMessageHandlerExtension
from ._base import BaseHandler
from ._states import FSM


class InitHandler(BaseHandler, OneTimeMessageHandlerExtension):
    async def handle(self) -> Any:
        await self.event.delete()
        self.clean_context()
        self._set_one_time_message(
            await self.event.answer('Пришли название файла')
        )
        await self.state.set_state(FSM.get_name)
