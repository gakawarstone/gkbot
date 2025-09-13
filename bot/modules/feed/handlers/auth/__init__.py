from aiogram import Router
from aiogram.filters import Command

from configs.commands import USER_COMMANDS
from ._states import FSM
from .start import GkfeedLoginInitHandler
from .get_login import LoginHandler
from .get_password import PasswordHandler


def setup(r: Router):
    r.message.register(GkfeedLoginInitHandler, Command(USER_COMMANDS.login_feed))
    r.message.register(LoginHandler, FSM.get_login)
    r.message.register(PasswordHandler, FSM.get_password)
