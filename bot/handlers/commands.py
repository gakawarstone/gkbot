from typing import Awaitable

from aiogram import Router
from aiogram.filters import Command

from . import start
from .user import bomber, braintrash, reminder
# from .user.road import road_to_the_dream as road # FIXME
from .user import shiki, tasks
from .user import text_to_speech as tts
from .user import wiki

users: dict[str, Awaitable] = {
    'add_task': tasks.add,
    'trash': braintrash.write,
    'start': start.start,
    'bomber': bomber.start,
    'add_remind': reminder.add,
    # 'road': road.start, # FIXME
    'tts': tts.start,
    'wiki': wiki.search,
    'shiki': shiki.updates.get_updates,
    'sub': shiki.subs.subscribe,
}


def setup(r: Router):
    for cmd in users:
        r.message.register(users[cmd], Command(commands=cmd))
