from typing import Optional
from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery, Message

from configs.env import GKFEED_USER, GKFEED_PASSWORD
from services.gkfeed import GkfeedService, FeedItem
from ..ui.keyboards import FeedMarkup


class BaseHandler(_BaseHandler[CallbackQuery | Message]):
    __gkfeed: Optional[GkfeedService] = None

    @property
    def _gkfeed(self) -> GkfeedService:
        if self.__gkfeed:
            return self.__gkfeed

        if GKFEED_USER is None or GKFEED_PASSWORD is None:
            raise ValueError("GKFEED_USER and GKFEED_PASSWORD must be set")

        self.__gkfeed = GkfeedService(GKFEED_USER, GKFEED_PASSWORD)
        return self.__gkfeed

    async def _send_item(self, item: FeedItem):
        if self.event.from_user is None:
            raise ValueError("from_user is required to send a message")
        await self.bot.send_message(
            self.event.from_user.id,
            f'<a href="{item.link}">Link</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    async def answer(self, *args, **kwargs):
        if isinstance(self.event, CallbackQuery):
            if self.event.message is None:
                raise ValueError("message is required for CallbackQuery.answer")
            return await self.event.message.answer(*args, **kwargs)
        return await self.event.answer(*args, **kwargs)
