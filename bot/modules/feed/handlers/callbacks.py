from typing import Any
import asyncio

from aiogram.types import CallbackQuery, InaccessibleMessage

from services.gkfeed.api import GkfeedApi
from services.gkfeed import GkfeedRequestError
from services.gkfeed.picker import GkfeedItemsPicker

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

        api = GkfeedApi(await self._gkfeed_credentials)

        match event:
            case FeedMarkup.data.delete:
                await api.delete_item_by_id(data)
                await self.event.message.delete()
            case FeedMarkup.data.keep:
                await self.event.message.delete()
            # NOTE: Deprecated
            case FeedMarkup.data.show_all_feed:
                pass
                # await self._send_items_from_feed(data)

    async def _send_one_feed_item(self):
        picker = GkfeedItemsPicker(await self._gkfeed_credentials)

        try:
            if item := await picker.get_next_item():
                await self._process_item(item)
            else:
                await self.answer("На данный момент ничего нового")
        except GkfeedRequestError:
            await self.answer("Не удалось загрузить ленту, попробуйте позже")

    # NOTE : Deprecated
    # async def _send_items_from_feed(self, feed_id: int, limit=10) -> None:
    #     picker = GkfeedItemsPicker(await self._gkfeed_credentials)
    #
    #     for _ in range(limit):
    #         item = await picker.get_next_item(lambda i: i.feed_id == feed_id)
    #
    #         if not item:
    #             break
    #
    #         await self._process_item(item)
