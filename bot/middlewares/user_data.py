from typing import Callable, Dict, Awaitable, Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject


class UserDataMiddleware(BaseMiddleware):
    __data: Dict[int, Dict[str, Any]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        user_id = user.id if user else None

        if user_id is None:
            raise ValueError("Event does not contain a user.")

        if user_id not in self.__data:
            self.__data[user_id] = {}
        data["data"] = self.__data[user_id]

        await handler(event, data)
