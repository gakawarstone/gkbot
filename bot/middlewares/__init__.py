from lib.bot import BotManager
from .register_user import RegisterUserMiddleware
from .user_data import UserDataMiddleware


def setup(mng: BotManager):
    mng.dp.message.middleware(RegisterUserMiddleware())
    mng.dp.message.middleware(UserDataMiddleware())
    pass
