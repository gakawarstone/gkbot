import asyncio
import logging
from functools import partial
from typing import Any

from aiogram.types import CallbackQuery, InaccessibleMessage

from services.gkfeed.api import GkfeedApi
from services.gkfeed.picker import GkfeedItemsPicker

from ..ui.keyboards import FeedMarkup
from ._base import BaseHandler
from ._item_processor import GkfeedItemProcessorExtension

logger = logging.getLogger(__name__)
# Keep API requests alive after the callback handler finishes.
_delete_tasks: set[asyncio.Task[None]] = set()


def _finish_item_deletion(item_id: int, task: asyncio.Task[None]) -> None:
    _delete_tasks.discard(task)
    if task.cancelled():
        logger.warning("Feed item deletion cancelled id=%s", item_id)
        return

    error = task.exception()
    if error is not None:
        logger.error(
            "Failed to delete feed item id=%s",
            item_id,
            exc_info=(type(error), error, error.__traceback__),
        )


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
        await self._handle_event(event, data)
        await self._send_one_feed_item()

    async def _handle_event(self, event: str, data: int) -> None:
        if not isinstance(self.event, CallbackQuery):
            raise ValueError("event must be CallbackQuery")

        if not self.event.message or isinstance(
            self.event.message, InaccessibleMessage
        ):
            raise ValueError("event must have message")

        match event:
            case FeedMarkup.data.delete:
                await self.event.message.delete()
                api = GkfeedApi(await self._gkfeed_credentials)
                task = asyncio.create_task(api.delete_item_by_id(data))
                _delete_tasks.add(task)
                task.add_done_callback(partial(_finish_item_deletion, data))
            case FeedMarkup.data.keep:
                await self.event.message.delete()
            # NOTE: Deprecated
            # NOTE: need to be replaced with general actions button
            case FeedMarkup.data.show_all_feed:
                pass
                # await self._send_items_from_feed(data)

    async def _send_one_feed_item(self) -> None:
        picker = GkfeedItemsPicker(await self._gkfeed_credentials)

        if item := await picker.get_next_item():
            await self._process_item(item)
        else:
            await self.answer("На данный момент ничего нового")

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
