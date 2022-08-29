from aiogram import Dispatcher

from .register_user import RegisterUserMiddleware
from .user_data import UserDataMiddleware


def setup(dp: Dispatcher):
    dp.message.middleware(RegisterUserMiddleware())
    dp.message.middleware(UserDataMiddleware())
