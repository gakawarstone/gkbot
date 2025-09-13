from typing import Any

from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from ._states import FSM


class GkfeedLoginInitHandler(OneTimeMessageHandlerExtension, BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        text = "Please enter your gkfeed login:"
        self._set_one_time_message(await self.event.answer(text))
        await self.state.set_state(FSM.get_login)
