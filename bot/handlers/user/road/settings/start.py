from typing import Any

from ui.keyboards.pomodoro import PomodoroSettingsMarkup
from services.repositories.road_settings import RoadSettingsRepository
from ._base import BaseHandler
from ..states import FSM


class InitSettingsHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.menu)
        if self.event.from_user is None:
            raise ValueError("from_user is None")

        user_id = self.event.from_user.id
        current_settings = await RoadSettingsRepository.get_user_settings(user_id)
        markup = PomodoroSettingsMarkup.get_settings_dialog(current_settings)
        await self.event.answer("Настройки", reply_markup=markup)
