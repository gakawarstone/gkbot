from typing import Callable, Any, Awaitable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message

from services.timezone import UserDontHaveTimeZone, TimeZone


class TimeZoneMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message, data: Dict[str, Any]
    ) -> Any:
        if not get_flag(data, 'require_timezone'):
            return await handler(event, data)

        try:
            data['data']['tz'] = await TimeZone.get_user_timezone(event.from_user.id)
            await handler(event, data)
        except UserDontHaveTimeZone:
            await event.answer('Необходима таймзона /set_tz')
