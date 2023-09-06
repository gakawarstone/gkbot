from aiogram import Router

from . import text_to_speech as tts
from . import tasks
from . import braintrash
from . import bomber
from . import reminder
from . import road
from . import wiki
from . import shiki
from . import admins as adm
from . import timer
from . import books
from . import timezone
from . import list
from . import platonus2indigo
from . import download
from . import asura


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
    timezone.setup(r)
    list.setup(r)
    platonus2indigo.setup(r)
    download.setup(r)
    asura.setup(r)
