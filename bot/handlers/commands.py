from dataclasses import dataclass
from typing import Awaitable
from aiogram.dispatcher.filters.state import State

from lib.bot import BotManager
from .user import text_to_speech as tts


@dataclass
class CommandHandler:
    callback: Awaitable
    context: State


users: dict[str, CommandHandler] = {
    # 'add_task': tasks.add,
    # 'trash': braintrash.write,
    # 'start': hello.start,
    # 'bomber': bomber.start,
    # 'add_remind': reminder.add,
    # 'road': road.start,
    'tts': tts.start,
    # 'wiki': wiki.search,
    # 'shiki': shiki.get_updates,
    # 'sub': shiki.subscribe,
    # 'start_timer': timer.start,
    # 'stop_timer': timer.stop,
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
