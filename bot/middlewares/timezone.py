from typing import Callable, Any, Awaitable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject


class TimeZoneMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[
                           [TelegramObject, Dict[str, Any]], Awaitable[Any]
                       ],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        data['tz'] = 6.0  # FIXME
        return await super().__call__(handler, event, data)
