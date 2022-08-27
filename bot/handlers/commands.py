from typing import Awaitable

from lib.bot import BotManager

from . import start
from .user import bomber, braintrash, reminder
from .user import road_to_the_dream as road
from .user import shiki, tasks
from .user import text_to_speech as tts
from .user import wiki

users: dict[str, Awaitable] = {
    'add_task': tasks.add,
    'trash': braintrash.write,
    'start': start.start,
    'bomber': bomber.start,
    'add_remind': reminder.add,
    'road': road.start,
    'tts': tts.start,
    'wiki': wiki.search,
    'shiki': shiki.updates.get_updates,
    'sub': shiki.subs.subscribe,
}


def setup(mng: BotManager):
    for cmd in users:
        print(cmd, users[cmd])
        mng.add_command_handler(cmd, users[cmd])
