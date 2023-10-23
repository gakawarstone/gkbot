from typing import Any

from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from ._base import BaseHandler
from ._states import FSM


class GetNameHandler(BaseHandler, OneTimeMessageHandlerExtension):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        self.set(self.props.file_name, self.event.text)
        self._set_one_time_message(
            await self.event.answer("Пришли ссылку на файл который хочешь скачать")
        )
        await self.state.set_state(FSM.get_link)
