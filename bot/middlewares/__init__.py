from aiogram import Dispatcher

from .delete_queue import DeleteQueueMiddleware
from .not_enough_rights import NotEnoughRightsMiddleware
from .register_user import RegisterUserMiddleware
from .timezone import TimeZoneMiddleware
from .user_data import UserDataMiddleware


def setup(dp: Dispatcher):
    dp.message.middleware(RegisterUserMiddleware())
    dp.message.middleware(UserDataMiddleware())
    dp.message.middleware(TimeZoneMiddleware())
    dp.message.middleware(DeleteQueueMiddleware())
    dp.message.middleware(NotEnoughRightsMiddleware())

    dp.inline_query.middleware(RegisterUserMiddleware())

    dp.callback_query.middleware(UserDataMiddleware())
