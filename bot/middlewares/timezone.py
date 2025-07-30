from typing import Callable, Any, Awaitable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, TelegramObject

from services.timezone import UserDontHaveTimeZone, TimeZone


class TimeZoneMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Check if event is a Message and has from_user
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        if not get_flag(data, "require_timezone"):
            return await handler(event, data)

        try:
            user_id = event.from_user.id
            data["data"]["tz"] = await TimeZone.get_user_timezone(user_id)
            await handler(event, data)
        except UserDontHaveTimeZone:
            await event.answer("Необходима таймзона /set_tz")
