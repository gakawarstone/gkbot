from aiogram import Router
from aiogram.filters import Command, StateFilter

from configs.commands import USER_COMMANDS
from ._states import FSM
from .start import InitHandler
from .get_text import TextInputHandler
from .get_date import DateInputHandler
from .get_time import TimeInputHandler


def setup(r: Router):
    r.message.register(InitHandler, StateFilter(FSM.start))
    r.message.register(TextInputHandler, StateFilter(FSM.get_text))
    r.message.register(DateInputHandler, StateFilter(FSM.get_date))
    r.message.register(TimeInputHandler, StateFilter(FSM.get_time))
    r.message.register(InitHandler, Command(commands=USER_COMMANDS.add_remind))
