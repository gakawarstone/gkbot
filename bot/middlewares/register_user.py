from typing import Awaitable, Callable, Dict, Any

from aiogram.types import User
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject

from models.users import Users


class RegisterUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = getattr(event, "from_user", None)
        if not user:
            raise ValueError("Event does not contain a user")

        if not await Users.filter(user_id=user.id).first():
            await Users.create(
                user_id=user.id, user_name=getattr(user, "full_name", "")
            )

        await handler(event, data)
