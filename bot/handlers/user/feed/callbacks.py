import requests
import json
from typing import Any

from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery

from configs.env import GKFEED_PASSWORD, GKFEED_USER
from ui.keyboards.feed import FeedMarkup


class ItemEventHandler(_BaseHandler[CallbackQuery]):
    async def _parse_callback(self) -> int:
        _, _, item_id = self.event.data.split(":")
        return int(item_id)

    @property
    async def _item_id(self):
        return await self._parse_callback()

    async def handle(self) -> Any:
        print(self.event.data)
        if self.event.data.startswith(FeedMarkup.prefix + ":" + FeedMarkup.data.delete):
            headers = {"Content-Type": "application/json"}
            item_id = await self._item_id
            data = {
                "itemIds": [
                    item_id,
                ]
            }
            json_data = json.dumps(data)

            requests.post(
                "http://feed.gws.freemyip.com/api/v1/add_deleted_items",
                data=json_data,
                auth=(GKFEED_USER, GKFEED_PASSWORD),
                headers=headers,
            )
            await self.event.message.delete()

        if self.event.data.startswith(FeedMarkup.prefix + ":" + FeedMarkup.data.keep):
            await self.event.message.delete()
