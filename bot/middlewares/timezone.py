from typing import Any

from aiogram.dispatcher.flags import get_flag
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, TelegramObject

from services.timezone import TimeZone, UserDontHaveTimeZone

from .data import MiddlewareData, MiddlewareHandler, require_user_data


class TimeZoneMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        # Aiogram accepts dict[str, Any]; its docs recommend a TypedDict here.
        self,
        handler: MiddlewareHandler,
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        # Check if event is a Message and has from_user
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        if not get_flag(dict(data), "require_timezone"):
            return await handler(event, data)

        try:
            user_id = event.from_user.id
            require_user_data(data)["tz"] = await TimeZone.get_user_timezone(user_id)
            return await handler(event, data)
        except UserDontHaveTimeZone:
            await event.answer("Необходима таймзона /set_tz")
            return None
