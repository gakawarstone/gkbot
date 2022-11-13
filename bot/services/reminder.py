from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from aiogram import Bot

from lib.schedule import Schedule, Task


@dataclass
class Remind:
    user_id: int
    date_time: datetime
    text: str


class Reminder:
    @classmethod
    async def setup(cls, bot: Bot) -> None:
        cls.__bot = bot

    @classmethod
    def add_remind(cls, user_id: int, date_time: datetime, text: str) -> None:
        date_time_in_local = cls.__get_datetime_in_local_tz(date_time)
        remind = Remind(user_id, date_time_in_local, text)
        cls.__add_message_to_schedule(remind)

    @classmethod
    def __get_datetime_in_local_tz(cls, date_time: datetime) -> datetime:
        local_timezone = datetime.now(
            timezone(timedelta(0))).astimezone().tzinfo
        return date_time.astimezone(local_timezone)

    @classmethod
    def __add_message_to_schedule(cls, remind: Remind):
        Schedule.add_task(
            task=Task(
                func=cls.__bot.send_message,
                args=[remind.user_id, remind.text]
            ),
            time=remind.date_time
        )

    @classmethod
    def __add_to_db(cls):
        # TODO
        pass
