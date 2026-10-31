from datetime import timedelta

import pytest
from tortoise import Tortoise

from models.timezone import TimeZone as TimeZoneModel
from services.timezone import InvalidTimeZone, TimeZone, UserDontHaveTimeZone

INVALID_TZ_SET = [timedelta(hours=-12, minutes=-1), timedelta(hours=14, seconds=1)]

VALID_TZ_SET = [
    timedelta(hours=1),
    timedelta(hours=6),
    timedelta(hours=14),
    timedelta(hours=-12),
]


class MockedTimeZone(TimeZone):
    @classmethod
    async def _get_tz_by_user_id(cls, user_id: int) -> timedelta | None:  # type: ignore[override]
        if user_id > 1000:
            return timedelta(hours=1)
        return None

    @classmethod
    async def _set_tz_by_user_id(cls, user_id: int, tz: timedelta) -> None:
        pass


@pytest.mark.asyncio
async def test_user_dont_have_timezone() -> None:
    with pytest.raises(UserDontHaveTimeZone):
        await MockedTimeZone.get_user_timezone(100)


@pytest.mark.asyncio
async def test_set_invalid_timezone() -> None:
    for tz in INVALID_TZ_SET:
        with pytest.raises(InvalidTimeZone):
            await MockedTimeZone.set_user_timezone(1001, tz)

    for tz in VALID_TZ_SET:
        await MockedTimeZone.set_user_timezone(1001, tz)


async def test_timezone_create_update_and_utc_round_trip() -> None:
    await Tortoise.init(
        db_url="sqlite://:memory:", modules={"models": ["models.timezone"]}
    )
    try:
        await Tortoise.generate_schemas()
        await TimeZone.set_user_timezone(2, timedelta(hours=3))
        for offset in [
            timedelta(0),
            timedelta(0),
            timedelta(hours=5),
            timedelta(hours=-12),
        ]:
            await TimeZone.set_user_timezone(1, offset)
            assert await TimeZone.get_user_timezone(1) == offset
            assert await TimeZoneModel.filter(user_id=1).count() == 1
            assert await TimeZone.get_user_timezone(2) == timedelta(hours=3)
    finally:
        await Tortoise.close_connections()
