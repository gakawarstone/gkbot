from aiogram import Router

from . import habits, menu, pomodoro, settings, start


def setup(r: Router):
    start.setup(r)
    pomodoro.setup(r)
    habits.setup(r)
    menu.setup(r)
    settings.setup(r)
