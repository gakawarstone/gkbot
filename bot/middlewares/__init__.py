from aiogram import Dispatcher

from configs.user_data import USER_DATA_IDLE_TTL_SECONDS, USER_DATA_MAX_ENTRIES

from .delete_queue import DeleteQueueMiddleware
from .not_enough_rights import NotEnoughRightsMiddleware
from .register_user import RegisterUserMiddleware
from .timezone import TimeZoneMiddleware
from .user_data import UserDataMiddleware
from .user_data_store import UserDataStore


def setup(dp: Dispatcher) -> None:
    user_data = UserDataMiddleware(
        UserDataStore(
            max_entries=USER_DATA_MAX_ENTRIES,
            idle_ttl=USER_DATA_IDLE_TTL_SECONDS,
        )
    )
    dp.shutdown.register(user_data.close)
    dp.message.middleware(RegisterUserMiddleware())
    dp.message.middleware(user_data)
    dp.message.middleware(TimeZoneMiddleware())
    dp.message.middleware(DeleteQueueMiddleware())
    dp.message.middleware(NotEnoughRightsMiddleware())

    dp.inline_query.middleware(RegisterUserMiddleware())

    dp.callback_query.middleware(user_data)
