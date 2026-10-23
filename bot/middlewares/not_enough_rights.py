from typing import Any
from collections.abc import Awaitable, Callable

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject, Message
from aiogram.exceptions import TelegramBadRequest


class NotEnoughRightsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            if e.message == "Bad Request: message can't be deleted" and isinstance(
                event, Message
            ):
                await event.answer("Bot should can delete messages")
                return None
            raise
