from aiogram import Router

from . import admins as adm
from . import (
    asura,
    bomber,
    books,
    chatgpt,
    cvision,
    download,
    exit,
    list,
    platonus2indigo,
    reminder,
    road,
    sort_sources,
    timer,
    timezone,
    tts,
    wiki,
)


def setup(r: Router) -> None:
    # Register first so active FSM handlers cannot consume /exit as regular input.
    exit.setup(r)
    tts.setup(r)
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
