import asyncio
from typing import Any

from aiogram.types import Message


from services.gkfeed import GkfeedRequestError
from services.gkfeed.picker import GkfeedItemsPicker

from ._base import BaseHandler
from ._item_processor import GkfeedItemProcessorExtension


class ShowFeedItemsHandler(GkfeedItemProcessorExtension, BaseHandler):
    _items_limit = 1

    async def handle(self) -> Any:
        if not isinstance(self.event, Message):
            raise ValueError("event must be Message")

        await self.event.delete()

        picker = GkfeedItemsPicker(await self._gkfeed_credentials)

        try:
            try:
                async with asyncio.TaskGroup() as tg:
                    for _ in range(self._items_limit):
                        item = await picker.get_next_item()
                        print(item)

                        if not item:
                            break

                        tg.create_task(self._process_item(item))
            except* Exception as exc:
                for e in exc.exceptions:
                    raise e
        except GkfeedRequestError:
            await self.answer("Не удалось загрузить ленту, попробуйте позже")
