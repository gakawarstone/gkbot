from aiogram import Router

from . import tts
from . import tasks
from . import braintrash
from . import bomber
from . import reminder
from . import road
from . import wiki
from . import admins as adm
from . import timer
from . import books
from . import timezone
from . import list
from . import platonus2indigo
from . import download
from . import asura
from . import sort_sources
from . import cvision
from . import chatgpt
from . import exit


def setup(r: Router):
    # Register first so active FSM handlers cannot consume /exit as regular input.
    exit.setup(r)
    tts.setup(r)
    tasks.setup(r)
    braintrash.setup(r)
    bomber.setup(r)
    reminder.setup(r)
    road.setup(r)
    wiki.setup(r)
    adm.setup(r)
    timer.setup(r)
    books.setup(r)
    timezone.setup(r)
    list.setup(r)
    platonus2indigo.setup(r)
    download.setup(r)
    asura.setup(r)
    sort_sources.setup(r)
    cvision.setup(r)
    chatgpt.setup(r)
