from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, TelegramObject

from .data import MiddlewareData, MiddlewareHandler


class NotEnoughRightsMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        # Aiogram accepts dict[str, Any]; its docs recommend a TypedDict here.
        self,
        handler: MiddlewareHandler,
        event: TelegramObject,
        data: MiddlewareData,
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
