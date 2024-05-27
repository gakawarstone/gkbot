from datetime import datetime, timedelta

from aiogram import Router
from aiogram.types import Message

from core.notifier import Notifier
from services.schedule import Schedule, Task
from filters.command import CommandWithPrompt


async def init_handler(m: Message):
    minutes_to_wait = int(m.text.split(" ")[1])
    message_text = " ".join(m.text.split(" ")[1:])
    sending_time = datetime.now() + timedelta(minutes=minutes_to_wait)

    task = Task(func=Notifier.notify, args=[m.from_user.id, message_text])
    await Schedule.add_task(task, sending_time)
    await m.delete()


def setup(r: Router):
    r.message.register(init_handler, CommandWithPrompt("wait"))
