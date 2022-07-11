from dataclasses import dataclass
from typing import Awaitable
from aiogram.dispatcher.filters.state import State

from lib.bot import BotManager
from .user import text_to_speech as tts
from .user import tasks, timer
from .user import admins as adm
from . import start


users: dict[str, Awaitable] = {
    'add_task': tasks.add,
    # 'trash': braintrash.write,
    'start': start.start,
    # 'bomber': bomber.start,
    # 'add_remind': reminder.add,
    # 'road': road.start,
    'tts': tts.start,
    # 'wiki': wiki.search,
    # 'shiki': shiki.get_updates,
    # 'sub': shiki.subscribe,
    'start_timer': timer.start,
    'stop_timer': timer.stop,
    # 'admins': adm.tag_all_admins
}

admins = {
    # 'get_trash': braintrash.get_all_data,
}


def setup(mng: BotManager):
    for cmd in users:
        print(cmd, users[cmd])
        mng.add_command_handler(cmd, users[cmd])
    for cmd in admins:
        mng.add_command_handler(cmd, admins[cmd], admin_only=True)
