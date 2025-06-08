from aiogram import Router
from aiogram.filters import Command, StateFilter

from .._commands import USER_COMMANDS
from ._states import FSM
from .init import InitHandler
from .answer import AnswerHandler


def setup(r: Router):
    r.message.register(InitHandler, Command(USER_COMMANDS.chatgpt))
    r.message.register(AnswerHandler, StateFilter(FSM.get_message))
