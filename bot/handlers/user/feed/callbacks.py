from typing import Any

from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery

from configs.env import GKFEED_PASSWORD, GKFEED_USER
from services.gkfeed import GkfeedService
from ui.keyboards.feed import FeedMarkup


class ItemEventHandler(_BaseHandler[CallbackQuery]):
    __gkfeed = GkfeedService(GKFEED_USER, GKFEED_PASSWORD)

    async def _parse_callback(self) -> tuple[str, int]:
        _, event, data = self.event.data.split(":")
        return event, data

    async def handle(self) -> Any:
        event, data = await self._parse_callback()

        match event:
            case FeedMarkup.data.delete:
                item_id = int(data)
                await self.__gkfeed.delete_item_by_id(item_id)
                await self.event.message.delete()
            case FeedMarkup.data.keep:
                await self.event.message.delete()
            case FeedMarkup.data.show_all_feed:
                feed_id = int(data)
                await self._send_items_from_feed(feed_id)

    async def _send_items_from_feed(self, feed_id: int, limit=10) -> None:
        items_cnt = 0
        async for item in self.__gkfeed.get_items_from_feed(feed_id):
            if items_cnt > limit:
                break

            await self.event.message.answer(
                f'<a href="{item.link}">Link</a>',
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            )

            items_cnt += 1
