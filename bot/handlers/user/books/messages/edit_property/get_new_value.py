from typing import Any

from .change_property import ChangeBookPropertyHandler
from ._base import BaseHandler
from ._states import FSM


class GetNewPropertyValueHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        self.set(self.props.new_value, self.event.text)  # FIXME
        await ChangeBookPropertyHandler(self.event, state=self.state,
                                        data=self.user_data).handle()
