from typing import Awaitable, Callable, Dict, Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message


class DeleteQueueMiddleware(BaseMiddleware):
    async def __call__(
            self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message, data: Dict[str, Any]
    ) -> Any:
        if 'delete_queue' not in data['data'].keys():
            data['data']['delete_queue'] = []
        if len(messages := data['data']['delete_queue']) > 0:
            [await m.delete() for m in messages]
            data['data']['delete_queue'] = []
        await handler(event, data)
