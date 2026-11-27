from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.dispatcher.flags import get_flag
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, TelegramObject

from configs.commands import USER_COMMANDS
from services.timezone import TimeZone, UserDontHaveTimeZone


class TimeZoneMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Check if event is a Message and has from_user
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        if not get_flag(data, "require_timezone"):
            return await handler(event, data)

        try:
            user_id = event.from_user.id
            data["data"]["tz"] = await TimeZone.get_user_timezone(user_id)
            return await handler(event, data)
        except UserDontHaveTimeZone:
            await event.answer(f"Необходима таймзона /{USER_COMMANDS.set_tz}")
            return None
