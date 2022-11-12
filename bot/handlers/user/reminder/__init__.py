from aiogram import Router
from aiogram.filters import Command, StateFilter

from .._commands import USER_COMMANDS
from ._states import FSM
from .start import InitHandler
from .get_text import TextInputHandler
from .get_date import DateInputHandler
from .get_time import TimeInputHandler


def setup(r: Router):
    r.message.register(InitHandler, StateFilter(state=FSM.start))
    r.message.register(TextInputHandler, StateFilter(state=FSM.get_text))
    r.message.register(DateInputHandler, StateFilter(state=FSM.get_date))
    r.message.register(TimeInputHandler, StateFilter(state=FSM.get_time))
    r.message.register(InitHandler, Command(commands=USER_COMMANDS.add_remind))
