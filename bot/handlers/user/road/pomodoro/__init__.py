from aiogram import Router
from aiogram.filters import StateFilter

from .pomodoro import PomodoroHandler
from .restart import choose_bool
from ..states import FSM

__all__ = ["PomodoroHandler"]


def setup(r: Router):
    r.message.register(choose_bool, StateFilter(FSM.choose_bool))
