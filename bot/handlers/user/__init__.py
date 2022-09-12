from aiogram import Router

from . import text_to_speech as tts
from . import tasks
from . import braintrash
from . import bomber
from . import reminder
from . import road_to_the_dream as road
from . import wiki
from . import shiki
from . import admins as adm
from . import timer
from . import books


def setup(r: Router):
    tts.setup(r)
    tasks.setup(r)
    braintrash.setup(r)
    bomber.setup(r)
    reminder.setup(r)
    road.setup(r)
    wiki.setup(r)
    shiki.setup(r)
    adm.setup(r)
    timer.setup(r)
    books.setup(r)
