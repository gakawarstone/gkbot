from datetime import datetime

from tests.mocks.db import use_db
from services.schedule import TasksStorage
from services.reminder import Reminder


@use_db
async def test_remind_saving_in_db():
    dt = datetime.now()
    await Reminder.add_remind(1, dt, 'text')
    assert len(await TasksStorage().get_all()) == 1
