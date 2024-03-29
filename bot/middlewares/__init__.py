from aiogram import Dispatcher

from .register_user import RegisterUserMiddleware
from .user_data import UserDataMiddleware
from .timezone import TimeZoneMiddleware
from .delete_queue import DeleteQueueMiddleware
from .not_enough_rights import NotEnoughRightsMiddleware


def setup(dp: Dispatcher):
    dp.message.middleware(RegisterUserMiddleware())
    dp.message.middleware(UserDataMiddleware())
    dp.message.middleware(TimeZoneMiddleware())
    dp.message.middleware(DeleteQueueMiddleware())
    dp.message.middleware(NotEnoughRightsMiddleware())

    dp.inline_query.middleware(RegisterUserMiddleware())

    dp.callback_query.middleware(UserDataMiddleware())
