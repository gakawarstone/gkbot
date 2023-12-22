from typing import Awaitable, Callable, Dict, Any

from aiogram.types import Message, InlineQuery
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from models.users import Users

_Event = Message | InlineQuery


class RegisterUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[_Event, Dict[str, Any]], Awaitable[Any]],
        event: _Event,
        data: Dict[str, Any],
    ) -> Any:
        if not await Users.filter(user_id=event.from_user.id).first():
            await Users.create(
                user_id=event.from_user.id, user_name=event.from_user.full_name
            )
        await handler(event, data)
