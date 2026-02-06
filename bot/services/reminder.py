from dataclasses import dataclass
from datetime import datetime

from core.notifier import Notifier
from services.schedule import Schedule, Task


@dataclass
class Remind:
    user_id: int
    date_time: datetime
    text: str


class Reminder:
    @classmethod
    async def add_remind(cls, user_id: int, date_time: datetime, text: str):
        date_time_in_local = Schedule.to_local_tz(date_time)
        remind = Remind(user_id, date_time_in_local, text)
        await cls.__add_message_to_schedule(remind)

    @classmethod
    async def __add_message_to_schedule(cls, remind: Remind):
        await Schedule.add_task(
            task=Task(func=Notifier.notify, args=[remind.user_id, remind.text]),
            time=remind.date_time,
        )
