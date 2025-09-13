from typing import Any
import asyncio

from aiogram.types import CallbackQuery, InaccessibleMessage

from ..ui.keyboards import FeedMarkup
from ._base import BaseHandler
from ._item_processor import GkfeedItemProcessorExtension


class ItemEventHandler(GkfeedItemProcessorExtension, BaseHandler):
    async def _parse_callback(self) -> tuple[str, int]:
        data_str = getattr(self.event, "data", None)

        if not isinstance(data_str, str):
            raise ValueError("Callback data is required")

        parts = data_str.split(":")
        if len(parts) < 3:
            raise ValueError("Invalid callback data format")

        _, event, data = parts
        return event, int(data)

    async def handle(self) -> Any:
        event, data = await self._parse_callback()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._send_one_feed_item())
            tg.create_task(self._handle_event(event, data))

    async def _handle_event(self, event: str, data: int):
        if not isinstance(self.event, CallbackQuery):
            raise ValueError("event must be CallbackQuery")

        if not self.event.message or isinstance(
            self.event.message, InaccessibleMessage
        ):
            raise ValueError("event must have message")

        match event:
            case FeedMarkup.data.delete:
                await (await self._gkfeed()).delete_item_by_id(data)
                await self.event.message.delete()
            case FeedMarkup.data.keep:
                await self.event.message.delete()
            case FeedMarkup.data.show_all_feed:
                await self._send_items_from_feed(data)

    async def _send_one_feed_item(self):
        async for item in (await self._gkfeed()).get_all_user_items():
            print(item.id)
            await self._process_item(item)
            break

    async def _send_items_from_feed(self, feed_id: int, limit=10) -> None:
        items_cnt = 0
        async for item in (await self._gkfeed()).get_items_from_feed(feed_id):
            if items_cnt > limit:
                break

            await self._process_item(item)

            items_cnt += 1
