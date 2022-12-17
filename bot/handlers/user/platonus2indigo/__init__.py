from aiogram import Router
from aiogram.filters import Command, StateFilter

from .._commands import USER_COMMANDS
from ._states import FSM
from .start import init
from .convert_file import ConvertFileHandler


def setup(r: Router):
    r.message.register(init,
                       Command(commands=USER_COMMANDS.platonus2indigo))
    r.message.register(ConvertFileHandler, StateFilter(FSM.convert))
