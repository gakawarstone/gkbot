import asyncio

from aiogram.types import CallbackQuery, InaccessibleMessage

from services.gkfeed.api import GkfeedApi
from services.gkfeed.picker import GkfeedItemsPicker

from ..ui.keyboards import FeedMarkup
from ._base import BaseHandler
from ._item_processor import GkfeedItemProcessorExtension


class ItemEventHandler(GkfeedItemProcessorExtension, BaseHandler):
    async def _parse_callback(self) -> tuple[str, int]:
        data_str = getattr(self.event, "data", None)

        if not isinstance(data_str, str):
            raise TypeError("Callback data is required")

        parts = data_str.split(":")
        if len(parts) < 3:
            raise ValueError("Invalid callback data format")

        _, event, data = parts
        return event, int(data)

    async def handle(self) -> None:
        event, data = await self._parse_callback()
        if event not in (FeedMarkup.data.delete, FeedMarkup.data.keep):
            return

        await self._handle_event(event, data)
        await self._send_one_feed_item()

    async def _handle_event(self, event: str, data: int) -> None:
        if not isinstance(self.event, CallbackQuery):
            raise TypeError("event must be CallbackQuery")

        if not self.event.message or isinstance(
            self.event.message, InaccessibleMessage
        ):
            raise ValueError("event must have message")

        api = GkfeedApi(await self._gkfeed_credentials)

        match event:
            case FeedMarkup.data.delete:
                await self.event.message.delete()
                # BUG: can fail silently
                asyncio.create_task(api.delete_item_by_id(data))
            case FeedMarkup.data.keep:
                await self.event.message.delete()

    async def _send_one_feed_item(self) -> None:
        picker = GkfeedItemsPicker(await self._gkfeed_credentials)

        if item := await picker.get_next_item():
            await self._process_item(item)
        else:
            await self.answer("На данный момент ничего нового")
