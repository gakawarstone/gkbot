from settings import bot
from .register_user import RegisterUserMiddleware
from .user_data import UserDataMiddleware


def setup():
    bot.dp.middleware.setup(RegisterUserMiddleware())
    bot.dp.middleware.setup(UserDataMiddleware())
