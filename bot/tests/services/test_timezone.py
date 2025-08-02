from datetime import timedelta

import pytest

from services.timezone import TimeZone, UserDontHaveTimeZone, InvalidTimeZone

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
async def test_user_dont_have_timezone():
    with pytest.raises(UserDontHaveTimeZone):
        await MockedTimeZone.get_user_timezone(100)


@pytest.mark.asyncio
async def test_set_invalid_timezone():
    for tz in INVALID_TZ_SET:
        with pytest.raises(InvalidTimeZone):
            await MockedTimeZone.set_user_timezone(1001, tz)

    for tz in VALID_TZ_SET:
        await MockedTimeZone.set_user_timezone(1001, tz)
