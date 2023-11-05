from typing import Any

from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from ._states import FSM


class InitHandler(OneTimeMessageHandlerExtension, BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        text = (
            "Привет это новая функция сделанная потомучто <b>могу</b>\n\n"
            "Отправь мне сообщение и произойдет магия"
        )
        self._set_one_time_message(await self.event.answer(text))
        await self.state.set_state(FSM.send_speech)
