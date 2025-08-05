from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter

from configs.commands import USER_COMMANDS
from ._states import FSM
from .init import InitHandler
from .get_name import GetNameHandler
from .download import DownloadHandler

F: Message


def setup(r: Router):
    r.message.register(InitHandler, Command(USER_COMMANDS.dl))
    r.message.register(GetNameHandler, StateFilter(FSM.get_name))
    r.message.register(DownloadHandler, StateFilter(FSM.get_link))
