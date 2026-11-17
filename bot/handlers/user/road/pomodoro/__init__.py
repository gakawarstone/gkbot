from aiogram import Router
from aiogram.filters import StateFilter

from extensions.handlers.message.confirmation import choose_bool

from ..states import FSM
from .pomodoro import PomodoroHandler

__all__ = ["PomodoroHandler"]


def setup(r: Router):
    r.message.register(choose_bool, StateFilter(FSM.choose_bool))
