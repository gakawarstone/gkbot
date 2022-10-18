from aiogram import Router
from aiogram.filters import StateFilter

from .base import BaseHandler
from .pomodoro import PomodoroHandler
from .restart import ask_to_restart
from .restart import choose_bool
from ..states import FSM


def setup(r: Router):
    r.message.register(choose_bool, StateFilter(state=FSM.choose_bool))
