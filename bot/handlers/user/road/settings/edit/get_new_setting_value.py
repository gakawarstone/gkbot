import datetime
from datetime import time
from typing import Any

from services.repositories.road_settings import RoadSettingsRepository
from ...states import FSM
from .._context import RoadSettingsContextManager


class InvalidTimeInput(Exception):
    '''invalid time string'''


class GetNewSettingValueHandler(RoadSettingsContextManager):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        value = self._validate_time(self.event.text)
        user_id = self.event.from_user.id
        self.set(self.props.setting_new_value, value)
        await RoadSettingsRepository.update_user_setting(
            user_id, self.ctx.setting_name, self.ctx.setting_new_value)
        await self.event.answer('Изменено')
        await self.state.set_state(FSM.menu)

    # FIX: from reminder move to contrib
    def _validate_time(self, _time: str) -> time:
        try:
            tzinfo = datetime.timezone.utc
            return time(minute=int(_time), tzinfo=tzinfo)
        except ValueError:
            raise InvalidTimeInput
