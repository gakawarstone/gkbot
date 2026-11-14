from datetime import datetime, timedelta

from aiogram import Router
from aiogram.types import Message

from configs.commands import USER_COMMANDS
from core.notifier import Notifier
from filters.command import CommandWithPrompt
from services.schedule import Schedule, Task


async def init_handler(m: Message) -> None:
    if not m.text or not m.from_user:
        raise ValueError("Invalid message or user data")

    minutes_to_wait = int(m.text.split(" ")[1])
    message_text = " ".join(m.text.split(" ")[1:])
    sending_time = datetime.now() + timedelta(minutes=minutes_to_wait)

    task = Task(func=Notifier.notify, args=[m.from_user.id, message_text])
    await Schedule.add_task(task, sending_time)
    await m.delete()


def setup(r: Router) -> None:
    r.message.register(init_handler, CommandWithPrompt(USER_COMMANDS.wait))
