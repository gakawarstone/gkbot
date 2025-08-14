from typing import Any
from aiogram.types import CallbackQuery

from configs.env import GKFEED_USER, GKFEED_PASSWORD
from services.gkfeed import GkfeedService, FeedItem
from extensions.handlers.base import BaseHandler as _ExtensionsBaseHandler
from ..ui.keyboards import FeedMarkup

if not GKFEED_USER or not GKFEED_PASSWORD:
    raise ValueError("Gkfeed is not configured")


class BaseHandler(_ExtensionsBaseHandler):
    _gkfeed = GkfeedService(GKFEED_USER, GKFEED_PASSWORD)

    async def _send_item(self, item: FeedItem):
        if self.event.from_user is None:
            raise ValueError("from_user is required to send a message")
        await self.bot.send_message(
            self.event.from_user.id,
            f'<a href="{item.link}">Link</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    async def answer(self, *args: Any, **kwargs: Any):
        if isinstance(self.event, CallbackQuery):
            if self.event.message is None:
                raise ValueError("message is required for CallbackQuery.answer")
            return await self.event.message.answer(*args, **kwargs)
        return await self.event.answer(*args, **kwargs)

    async def answer_photo(self, *args: Any, **kwargs: Any):
        if isinstance(self.event, CallbackQuery):
            if self.event.message is None:
                raise ValueError("message is required for CallbackQuery.answer_photo")
            return await self.event.message.answer_photo(*args, **kwargs)
        return await self.event.answer_photo(*args, **kwargs)

    async def answer_video(self, *args: Any, **kwargs: Any):
        if isinstance(self.event, CallbackQuery):
            if self.event.message is None:
                raise ValueError("message is required for CallbackQuery.answer_video")
            return await self.event.message.answer_video(*args, **kwargs)
        return await self.event.answer_video(*args, **kwargs)
