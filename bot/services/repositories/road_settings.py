from datetime import time
from typing import Any

from configs import db
from models.road import RoadSettings as Model
from services.entities.road_settings import RoadSettings

DEFAULT_SETTINGS = RoadSettings(
    time_focused=time(minute=15),
    time_relax=time(minute=15),
)


class RoadSettingsRepository:
    @classmethod
    async def get_user_settings(cls, user_id: int) -> RoadSettings:
        async with db.SessionLocal() as session:
            settings = await session.get(Model, user_id)
            if not settings:
                return DEFAULT_SETTINGS
            return RoadSettings(settings.time_focused, settings.time_relax)

    @classmethod
    async def set_user_settings(cls, user_id: int, settings: RoadSettings) -> None:
        async with db.SessionLocal() as session:
            existing = await session.get(Model, user_id)
            if existing:
                existing.time_focused = settings.time_focused
                existing.time_relax = settings.time_relax
            else:
                new_settings = Model(
                    user_id=user_id,
                    time_focused=settings.time_focused,
                    time_relax=settings.time_relax,
                )
                session.add(new_settings)
            await session.commit()

    @classmethod
    async def update_user_setting(
        cls, user_id: int, setting_name: str, new_setting_value: Any
    ) -> None:
        async with db.SessionLocal() as session:
            existing = await session.get(Model, user_id)
            if not existing:
                new_settings = Model(
                    user_id=user_id,
                    time_focused=DEFAULT_SETTINGS.time_focused,
                    time_relax=DEFAULT_SETTINGS.time_relax,
                )
                session.add(new_settings)
                existing = new_settings
            setattr(existing, setting_name, new_setting_value)
            await session.commit()
