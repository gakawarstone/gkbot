from aiogram import Router
from aiogram.filters import StateFilter, Command

from configs.commands import USER_COMMANDS
from ._states import FSM
from .init import InitHandler
from .send_speech import SendSpeechHandler


def setup(r: Router):
    r.message.register(InitHandler, Command(commands=USER_COMMANDS.tts))
    r.message.register(SendSpeechHandler, StateFilter(FSM.send_speech))
