from datetime import time
from typing import Any

from models.road import RoadSettings as Model
from services.entities.road_settings import RoadSettings

DEFAULT_SETTINGS = RoadSettings(
    time_focused=time(minute=15),
    time_relax=time(minute=15),
)


class RoadSettingsRepository:
    @classmethod
    async def get_user_settings(cls, user_id: int) -> RoadSettings:
        settings = await Model.filter(user_id=user_id).first()
        if not settings:
            return DEFAULT_SETTINGS
        return RoadSettings(settings.time_focused, settings.time_relax)

    @classmethod
    async def set_user_settings(cls, user_id: int, settings: RoadSettings) -> None:
        await Model.update_or_create(
            user_id=user_id,
            time_focused=settings.time_focused,
            time_relax=settings.time_relax
        )

    @classmethod
    async def update_user_setting(
        cls, user_id: int,
        setting_name: str,
        new_setting_value: Any
    ) -> None:
        if not await Model.filter(user_id=user_id).first():
            await cls.set_user_settings(user_id, DEFAULT_SETTINGS)

        kwargs = {setting_name: new_setting_value}
        await Model.filter(user_id=user_id).update(**kwargs)
