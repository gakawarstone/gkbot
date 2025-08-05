from typing import Any
import asyncio

from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery

from ..ui.keyboards import FeedMarkup
from ._base import BaseHandler
from ._item_processor import GkfeedItemProcessorExtension


class ItemEventHandler(
    GkfeedItemProcessorExtension, BaseHandler, _BaseHandler[CallbackQuery]
):
    async def _parse_callback(self) -> tuple[str, int]:
        _, event, data = self.event.data.split(":")
        return event, data

    async def handle(self) -> Any:
        event, data = await self._parse_callback()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._send_one_feed_item())
            tg.create_task(self._handle_event(event, data))

    async def _handle_event(self, event: str, data: int):
        match event:
            case FeedMarkup.data.delete:
                item_id = int(data)
                await self._gkfeed.delete_item_by_id(item_id)
                await self.event.message.delete()
            case FeedMarkup.data.keep:
                await self.event.message.delete()
            case FeedMarkup.data.show_all_feed:
                feed_id = int(data)
                await self._send_items_from_feed(feed_id)

    async def _send_one_feed_item(self):
        async for item in self._gkfeed.get_all_user_items():
            print(item.id)
            await self._process_item(item)
            break

    async def _send_items_from_feed(self, feed_id: int, limit=10) -> None:
        items_cnt = 0
        async for item in self._gkfeed.get_items_from_feed(feed_id):
            if items_cnt > limit:
                break

            await self._process_item(item)

            items_cnt += 1
