from aiogram import Router
from aiogram.filters import StateFilter, Command

from .._commands import USER_COMMANDS
from ._states import FSM
from .init import InitHandler
from .send_speach import SendSpeachHandler


def setup(r: Router):
    r.message.register(InitHandler, Command(commands=USER_COMMANDS.tts))
    r.message.register(SendSpeachHandler, StateFilter(FSM.send_speach))
