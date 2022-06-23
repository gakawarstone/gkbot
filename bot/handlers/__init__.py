from . import bomber, braintrash, hello, reminder
from . import road_to_the_dream as road
from . import shiki, tasks
from . import text_to_speech as tts
from . import wiki
from . import channel
from . import timer

users = {
    'add_task': tasks.add,
    'trash': braintrash.write,
    'start': hello.start,
    'bomber': bomber.start,
    'add_remind': reminder.add,
    'road': road.start,
    'tts': tts.start,
    'wiki': wiki.search,
    'shiki': shiki.get_updates,
    'sub': shiki.subscribe,
    'start_timer': timer.start,
    'stop_timer': timer.stop,
}

admins = {
    'get_trash': braintrash.get_all_data,
}

channels = [
    channel.echo_post,
]
