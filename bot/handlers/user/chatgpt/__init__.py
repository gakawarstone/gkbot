from aiogram import Router
from aiogram.filters import Command, StateFilter

from configs.commands import USER_COMMANDS

from ._states import FSM
from .init import InitHandler
from .answer import AnswerHandler
from . import exit


def setup(r: Router):
    r.message.register(InitHandler, Command(USER_COMMANDS.chat))
    exit.setup(r)
    r.message.register(AnswerHandler, StateFilter(FSM.get_message))
