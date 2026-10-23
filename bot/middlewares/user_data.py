from typing import Any, ClassVar

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject

from .data import MiddlewareData, MiddlewareHandler, UserData


class UserDataMiddleware(BaseMiddleware):
    __data: ClassVar[dict[int, UserData]] = {}

    async def __call__(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        # Aiogram accepts dict[str, Any]; its docs recommend a TypedDict here.
        self,
        handler: MiddlewareHandler,
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        user = getattr(event, "from_user", None)
        user_id = user.id if user else None

        if user_id is None:
            raise ValueError("Event does not contain a user.")

        if user_id not in self.__data:
            self.__data[user_id] = {"delete_queue": []}
        data["data"] = self.__data[user_id]

        return await handler(event, data)
