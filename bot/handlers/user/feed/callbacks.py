from typing import Any

from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery

from ui.keyboards.feed import FeedMarkup
from ._base import BaseHandler


class ItemEventHandler(BaseHandler, _BaseHandler[CallbackQuery]):
    async def _parse_callback(self) -> tuple[str, int]:
        _, event, data = self.event.data.split(":")
        return event, data

    async def handle(self) -> Any:
        event, data = await self._parse_callback()

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
