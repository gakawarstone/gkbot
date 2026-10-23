import logging
from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramUnauthorizedError,
)
from aiogram.types import Message, TelegramObject

from .data import MiddlewareData, MiddlewareHandler, require_user_data

logger = logging.getLogger(__name__)

# Telegram errors for which a queued message is treated as undeletable
# (already deleted, inaccessible, or bot has no rights) and dropped
# instead of blocking the queue.
UNDELETABLE_MESSAGE_ERRORS = (
    TelegramBadRequest,
    TelegramNotFound,
    TelegramForbiddenError,
    TelegramUnauthorizedError,
)


class DeleteQueueMiddleware(BaseMiddleware):
    """Delete queued messages before handling the update.

    The pending batch is detached up front, so a single failing ("poison")
    message can never block later updates.
    """

    async def __call__(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        # Aiogram accepts dict[str, Any]; its docs recommend a TypedDict here.
        self,
        handler: MiddlewareHandler,
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        for message in self._detach_batch(data):
            await self._try_delete(message)
        return await handler(event, data)

    @staticmethod
    def _detach_batch(data: MiddlewareData) -> list[Message]:
        """Take ownership of pending deletions, leaving a fresh queue behind."""
        queue = require_user_data(data).setdefault("delete_queue", [])
        batch = list(queue)
        queue.clear()
        return batch

    @staticmethod
    async def _try_delete(message: Message) -> None:
        try:
            await message.delete()
        except UNDELETABLE_MESSAGE_ERRORS as error:
            logger.warning("Skipping undeletable queued message: %s", error)
