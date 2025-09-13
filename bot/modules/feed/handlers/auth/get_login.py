from typing import Any

from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from modules.feed.handlers.auth._states import FSM


class LoginHandler(OneTimeMessageHandlerExtension, BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        await self.state.update_data(login=self.event.text)

        text = "Please enter your password:"
        self._set_one_time_message(await self.event.answer(text))
        await self.state.set_state(FSM.get_password)
