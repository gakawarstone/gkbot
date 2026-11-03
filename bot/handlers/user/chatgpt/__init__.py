from aiogram import Router
from aiogram.filters import Command, StateFilter

from configs.commands import USER_COMMANDS

from . import exit
from ._generation import stop_generation
from ._states import FSM
from .answer import AnswerHandler
from .init import InitHandler


def setup(r: Router) -> None:
    r.stopped_message_generation.register(stop_generation)
    r.message.register(InitHandler, Command(USER_COMMANDS.chat))
    exit.setup(r)
    r.message.register(AnswerHandler, StateFilter(FSM.get_message))
