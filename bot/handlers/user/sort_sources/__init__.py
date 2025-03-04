from aiogram import Router
from aiogram.filters import Command, StateFilter

from .._commands import USER_COMMANDS
from ._states import FSM
from .start import InitHandler
from .sort_file import SortFileHandler


def setup(r: Router):
    r.message.register(InitHandler, Command(commands=USER_COMMANDS.sort_sources))
    r.message.register(SortFileHandler, StateFilter(FSM.sort_file))
