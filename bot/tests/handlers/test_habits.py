from datetime import time
from unittest.mock import AsyncMock

from sqlalchemy import select

from configs import db
from handlers.user.road.habits import get_habit_notify_time
from models.road import Habits
from tests.mocks.db import use_db
from tests.mocks.message import make_fake_message


@use_db
async def test_habit_notify_time_persists_habit() -> None:
    data = {"habit_name": "Read"}
    await get_habit_notify_time(make_fake_message("09:30"), AsyncMock(), data)

    async with db.SessionLocal() as session:
        habit = (await session.execute(select(Habits))).scalar_one()
        assert habit.user_id == 1
        assert habit.name == "Read"
        assert habit.notify_time == time(9, 30)
