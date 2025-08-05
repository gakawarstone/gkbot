from aiogram import Router
from aiogram.filters import Command, StateFilter


from configs.commands import USER_COMMANDS
from .add import AddFeedHandler
from ._states import FSM
from .init import InitAddFeedHandler


def setup(r: Router):
    r.message.register(InitAddFeedHandler, Command(USER_COMMANDS.add_feed))
    r.message.register(AddFeedHandler, StateFilter(FSM.get_url))
