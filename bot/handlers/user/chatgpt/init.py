from typing import Any, override

from ._base import BaseHandler
from ._states import FSM


class InitHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        self.clean_context()
        await self.event.answer("Что хочешь от меня?")
        await self.state.set_state(FSM.get_message)

    @override
    def clean_context(self, *args):
        super().clean_context(*args)
        self.set(self.props.messages, [])
