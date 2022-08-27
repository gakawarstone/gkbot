from typing import Callable, Dict, Awaitable, Any

from aiogram.types import Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class UserDataMiddleware(BaseMiddleware):
    __data = {}

    async def __call__(
            self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message, data: Dict[str, Any]) -> Any:
        if event.from_user.id not in self.__data:
            self.__data[event.from_user.id] = {}

        data['data'] = self.__data[event.from_user.id]
        await handler(event, data)
