import asyncio
from typing import Any


from extensions.handlers.message.base import BaseHandler as BaseMessageHandler
from ._base import BaseHandler
from ._item_processor import GkfeedItemProcessorExtension


class ShowFeedItemsHandler(
    GkfeedItemProcessorExtension, BaseHandler, BaseMessageHandler
):
    _items_limit = 1

    async def handle(self) -> Any:
        await self.event.delete()

        items_cnt = 0
        try:
            async with asyncio.TaskGroup() as tg:
                async for item in self._gkfeed.get_all_user_items():
                    if items_cnt >= self._items_limit:
                        break

                    tg.create_task(self._process_item(item))

                    items_cnt += 1
        except* Exception as exc:
            for e in exc.exceptions:
                raise e
