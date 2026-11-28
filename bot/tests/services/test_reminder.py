from datetime import datetime

import pytest

from services.reminder import Reminder
from services.schedule import TasksStorage
from tests.mocks.db import use_db


async def deliver_reminder(user_id: int, text: str) -> None:
    pass


@pytest.mark.asyncio
@use_db
async def test_remind_saving_in_db() -> None:
    dt = datetime.now()
    await Reminder.add_remind(1, dt, "text", deliver=deliver_reminder)
    assert len(await TasksStorage().get_all()) == 1
