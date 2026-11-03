from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

from configs.commands import USER_COMMANDS

from ._states import FSM
from .download import DownloadHandler
from .get_name import GetNameHandler
from .init import InitHandler

F: Message


def setup(r: Router):
    r.message.register(InitHandler, Command(USER_COMMANDS.dl))
    r.message.register(GetNameHandler, StateFilter(FSM.get_name))
    r.message.register(DownloadHandler, StateFilter(FSM.get_link))
