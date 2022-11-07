from dataclasses import dataclass
from datetime import datetime, time

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
        remind = Remind(user_id, date_time, text)
        cls.__add_message_to_schedule(remind)

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
    def add_remind_today(cls, user_id: int, time: time, text: str) -> None:
        # TODO
        pass

    @classmethod
    def __add_to_db(cls):
        # TODO
        pass
