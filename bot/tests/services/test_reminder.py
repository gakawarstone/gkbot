from datetime import datetime

import pytest

from services.reminder import Reminder
from services.schedule import TasksStorage
from tests.mocks.db import use_db


@pytest.mark.asyncio
@use_db
async def test_remind_saving_in_db():
    dt = datetime.now()
    await Reminder.add_remind(1, dt, "text")
    assert len(await TasksStorage().get_all()) == 1
