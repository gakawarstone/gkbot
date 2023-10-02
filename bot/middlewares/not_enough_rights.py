from typing import Awaitable, Callable, Dict, Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest


class NotEnoughRightsMiddleware(BaseMiddleware):
    async def __call__(
            self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message, data: Dict[str, Any]
    ) -> Any:
        try:
            await handler(event, data)
        except TelegramBadRequest as e:
            if e.message == 'Bad Request: message can\'t be deleted':
                await event.answer('Bot should can delete messages')
            else:
                raise e
