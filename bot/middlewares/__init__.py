from settings import bot
from .register_user import RegisterUserMiddleware


def setup():
    bot.dp.middleware.setup(RegisterUserMiddleware())
