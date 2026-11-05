from aiogram import Router

from . import menu, pomodoro, settings, start


def setup(r: Router):
    start.setup(r)
    pomodoro.setup(r)
    menu.setup(r)
    settings.setup(r)
