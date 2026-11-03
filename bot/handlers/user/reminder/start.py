from typing import Any

from extensions.handlers.message.use_timezone_extension import (
    UseTimeZoneHandlerExtension,
)
from ui.components.remind_creator import RemindCreator

from ._base import BaseHandler
from ._states import FSM


# NOTE: type ignore because of UseTimeZoneHandlerExtension
class InitHandler(BaseHandler, UseTimeZoneHandlerExtension):  # type: ignore[misc]
    async def handle(self) -> Any:
        await self.state.set_state(FSM.get_text)
        await self.event.delete()
        self.clean_context(self.keys.tz)
        self.set(self.keys.tz, self.tz)
        text = RemindCreator().render()
        self.set(self.keys.message, (await self.event.answer(text)))
