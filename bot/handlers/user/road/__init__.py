from aiogram import Router

from . import habits
from . import menu
from . import pomodoro
from . import start
from . import settings


def setup(r: Router):
    start.setup(r)
    pomodoro.setup(r)
    habits.setup(r)
    menu.setup(r)
    settings.setup(r)
