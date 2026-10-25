from aiogram import Router
from aiogram.filters import Command, StateFilter

from configs.commands import USER_COMMANDS

from ._states import FSM
from .sort_file import SortFileHandler
from .start import InitHandler


def setup(r: Router):
    r.message.register(InitHandler, Command(commands=USER_COMMANDS.sort_sources))
    r.message.register(SortFileHandler, StateFilter(FSM.sort_file))
