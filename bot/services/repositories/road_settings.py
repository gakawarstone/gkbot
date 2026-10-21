from datetime import time
from typing import Any
from sqlalchemy import select, update

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
            stmt = select(Model).where(Model.user_id == user_id)
            result = await session.execute(stmt)
            settings = result.scalar_one_or_none()
            if not settings:
                return DEFAULT_SETTINGS
            return RoadSettings(settings.time_focused, settings.time_relax)

    @classmethod
    async def set_user_settings(cls, user_id: int, settings: RoadSettings) -> None:
        async with db.SessionLocal() as session:
            stmt = select(Model).where(Model.user_id == user_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.time_focused = settings.time_focused
                existing.time_relax = settings.time_relax
            else:
                new_settings = Model(
                    user_id=user_id,
                    time_focused=settings.time_focused,
                    time_relax=settings.time_relax
                )
                session.add(new_settings)
            await session.commit()

    @classmethod
    async def update_user_setting(
        cls, user_id: int,
        setting_name: str,
        new_setting_value: Any
    ) -> None:
        async with db.SessionLocal() as session:
            stmt = select(Model).where(Model.user_id == user_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if not existing:
                new_settings = Model(
                    user_id=user_id,
                    time_focused=DEFAULT_SETTINGS.time_focused,
                    time_relax=DEFAULT_SETTINGS.time_relax
                )
                setattr(new_settings, setting_name, new_setting_value)
                session.add(new_settings)
            else:
                setattr(existing, setting_name, new_setting_value)
            await session.commit()
