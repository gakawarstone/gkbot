from typing import Any

from extensions.handlers.callback.base import BaseHandler
from ._context import RoadSettingsContextManager
from ..states import FSM


class EditSettingsHandler(BaseHandler, RoadSettingsContextManager):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        setting_name = self._parse_callback()
        self.clean_context()
        self.set(self.props.setting_name, setting_name)

        await self.event.message.answer(f"Введите новое значение для {setting_name}")
        await self.state.set_state(FSM.get_new_setting_value)

    def _parse_callback(self) -> str:
        if not self.event.data:
            raise ValueError("Empty callback: ", self.event)

        _, setting_name = self.event.data.split(":")
        return setting_name
