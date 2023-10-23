from datetime import time

from extensions.handlers.message.base import BaseHandler as _BaseHandler
from services.repositories.road_settings import RoadSettingsRepository, RoadSettings
from ui.widgets.timer import Timer


class BaseHandler(_BaseHandler):
    @property
    async def settings(self) -> RoadSettings:
        user_id = self.event.from_user.id
        settings = await RoadSettingsRepository.get_user_settings(user_id)
        return settings

    async def run_timer(self, time: time, greet_text: str, timer_text: str):
        msg = await self.event.answer(greet_text)
        seconds = self._convert_time_to_seconds(time)
        await Timer(self.event, seconds, timer_text).run()
        await msg.delete()

    @staticmethod
    def _convert_time_to_seconds(time: time) -> int:
        return time.hour * 60 * 60 + time.minute * 60 + time.second
