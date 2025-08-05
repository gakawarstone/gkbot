from typing import Any

from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from ._base import BaseHandler
from ._const import ADD_FEED_MESSAGE
from ._states import FSM


class InitAddFeedHandler(BaseHandler, OneTimeMessageHandlerExtension):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_url)
        await self.event.delete()
        self._set_one_time_message(await self.event.answer(ADD_FEED_MESSAGE))

