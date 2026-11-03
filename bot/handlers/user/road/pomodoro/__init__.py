from aiogram import Router
from aiogram.filters import StateFilter

from ..states import FSM
from .pomodoro import PomodoroHandler
from .restart import choose_bool

__all__ = ["PomodoroHandler"]


def setup(r: Router):
    r.message.register(choose_bool, StateFilter(FSM.choose_bool))
