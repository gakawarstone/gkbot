from datetime import timedelta
from typing import Optional
from sqlalchemy import select, delete

from configs import db
from models.timezone import TimeZone as _TimeZone

_MIN_TZ = timedelta(hours=-12).total_seconds()
_MAX_TZ = timedelta(hours=14).total_seconds()


class UserDontHaveTimeZone(Exception):
    "User isn't register in TimeZone database"


class InvalidTimeZone(Exception):
    "Valid timezone from -12 to +14 hours"


class TimeZone:
    @classmethod
    async def get_user_timezone(cls, user_id: int) -> timedelta:
        if not (tz := await cls._get_tz_by_user_id(user_id)):
            raise UserDontHaveTimeZone
        return tz

    @classmethod
    async def _get_tz_by_user_id(cls, user_id: int) -> Optional[timedelta]:
        async with db.SessionLocal() as session:
            stmt = select(_TimeZone).where(_TimeZone.user_id == user_id)
            result = await session.execute(stmt)
            tzinfo = result.scalar_one_or_none()
            if tzinfo is None:
                return None
            return tzinfo.tz

    @classmethod
    async def set_user_timezone(cls, user_id: int, tz: timedelta) -> None:
        if not cls.__validate_timezone(tz):
            raise InvalidTimeZone
        await cls._set_tz_by_user_id(user_id, tz)

    @classmethod
    def __validate_timezone(cls, tz: timedelta) -> bool:
        seconds = tz.total_seconds()
        return _MIN_TZ <= seconds and seconds <= _MAX_TZ

    @classmethod
    async def _set_tz_by_user_id(cls, user_id: int, tz: timedelta) -> None:
        async with db.SessionLocal() as session:
            # Check if exists
            stmt = select(_TimeZone).where(_TimeZone.user_id == user_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.tz = tz
            else:
                new_tz = _TimeZone(user_id=user_id, tz=tz)
                session.add(new_tz)
            await session.commit()
