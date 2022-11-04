from datetime import timedelta
from typing import Optional

from models.timezone import TimeZone as _TimeZone

_MIN_TZ = timedelta(hours=-12).total_seconds()
_MAX_TZ = timedelta(hours=14).total_seconds()


class UserDontHaveTimeZone(Exception):
    'User isn\'t register in TimeZone database'


class InvalidTimeZone(Exception):
    'Valid timezone from -12 to +14 hours'


class TimeZone:
    @classmethod
    async def get_user_timezone(cls, user_id: int) -> timedelta:
        if not (tz := await cls._get_tz_by_user_id(user_id)):
            raise UserDontHaveTimeZone
        return tz

    @classmethod
    async def _get_tz_by_user_id(cls, user_id: int) -> Optional[timedelta]:
        tzinfo = await _TimeZone.filter(user_id=user_id).first()
        if not type(tzinfo) == _TimeZone:
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
        await _TimeZone.update_or_create(user_id=user_id, tz=tz)
