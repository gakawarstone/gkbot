from aiogram import Router
from aiogram.filters import Command, StateFilter

from configs.commands import USER_COMMANDS

from ._states import FSM
from .convert_file import ConvertFileHandler
from .start import init


def setup(r: Router):
    r.message.register(init,
                       Command(commands=USER_COMMANDS.platonus2indigo))
    r.message.register(ConvertFileHandler, StateFilter(FSM.convert))
