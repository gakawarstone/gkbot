from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject, User

from models.users import Users

from .data import MiddlewareData, MiddlewareHandler


class RegisterUserMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        # Aiogram accepts dict[str, Any]; its docs recommend a TypedDict here.
        self,
        handler: MiddlewareHandler,
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        user: User | None = getattr(event, "from_user", None)
        if not user:
            raise ValueError("Event does not contain a user")

        if not await Users.filter(user_id=user.id).first():
            await Users.create(
                user_id=user.id, user_name=getattr(user, "full_name", "")
            )

        return await handler(event, data)
