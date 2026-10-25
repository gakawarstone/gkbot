import asyncio
import logging
from typing import Any

from aiogram.types import Message

from services.gkfeed.picker import GkfeedItemsPicker

from ._base import BaseHandler
from ._item_processor import GkfeedItemProcessorExtension

logger = logging.getLogger(__name__)


class ShowFeedItemsHandler(GkfeedItemProcessorExtension, BaseHandler):
    _items_limit = 1

    async def handle(self) -> Any:
        if not isinstance(self.event, Message):
            raise ValueError("event must be Message")

        await self.event.delete()

        picker = GkfeedItemsPicker(await self._gkfeed_credentials)

        try:
            async with asyncio.TaskGroup() as tg:
                for _ in range(self._items_limit):
                    item = await picker.get_next_item()

                    if not item:
                        await self.answer("На данный момент ничего нового")
                        break

                    logger.info(
                        "Processing feed item id=%s feed_id=%s text_length=%s",
                        item.id,
                        item.feed_id,
                        len(item.text),
                    )
                    tg.create_task(self._process_item(item))
        except* Exception as exc:
            for e in exc.exceptions:
                raise e
