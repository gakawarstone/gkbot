# from . import bomber, braintrash, hello, reminder
# from . import road_to_the_dream as road
# from . import shiki, tasks
# from . import text_to_speech as tts
# from . import wiki
# from . import channel
# from . import timer
# from . import admins as adm

from dataclasses import dataclass
from sre_parse import State
from typing import Awaitable
from aiogram.dispatcher.filters.state import State
from . import text_to_speech as tts


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
    'tts': [tts.start, tts.FSM.start],
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

channels = [
    # chnnel.echo_post,
]
