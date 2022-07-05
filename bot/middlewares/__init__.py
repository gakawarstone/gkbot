from settings import bot
from .register_user import RegisterUserMiddleware
from .user_data import UserDataMiddleware


def setup():
    bot.dp.message.middleware(RegisterUserMiddleware())
    bot.dp.message.middleware(UserDataMiddleware())
