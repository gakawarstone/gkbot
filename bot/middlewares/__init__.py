from aiogram import Dispatcher

from .register_user import RegisterUserMiddleware
from .user_data import UserDataMiddleware
from .timezone import TimeZoneMiddleware


def setup(dp: Dispatcher):
    dp.message.middleware(RegisterUserMiddleware())
    dp.message.middleware(UserDataMiddleware())
    dp.callback_query.middleware(UserDataMiddleware())
    dp.message.middleware(TimeZoneMiddleware())
