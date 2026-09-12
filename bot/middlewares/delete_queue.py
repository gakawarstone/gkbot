import logging
from typing import Awaitable, Callable, Dict, Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramUnauthorizedError,
)
from aiogram.types import Message, TelegramObject

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

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        for message in self._detach_batch(data):
            await self._try_delete(message)
        return await handler(event, data)

    @staticmethod
    def _detach_batch(data: Dict[str, Any]) -> list[Message]:
        """Take ownership of pending deletions, leaving a fresh queue behind."""
        queue = data["data"].setdefault("delete_queue", [])
        batch = list(queue)
        queue.clear()
        return batch

    @staticmethod
    async def _try_delete(message: Message) -> None:
        try:
            await message.delete()
        except UNDELETABLE_MESSAGE_ERRORS as error:
            logger.warning("Skipping undeletable queued message: %s", error)
