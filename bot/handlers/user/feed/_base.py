from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery

from configs.env import GKFEED_USER, GKFEED_PASSWORD
from services.gkfeed import GkfeedService, FeedItem
from ui.keyboards.feed import FeedMarkup


def _get_gkfeed() -> GkfeedService:
    if GKFEED_USER is None or GKFEED_PASSWORD is None:
        raise ValueError("GKFEED_USER and GKFEED_PASSWORD must be set")
    return GkfeedService(GKFEED_USER, GKFEED_PASSWORD)


class BaseHandler(_BaseHandler):
    _gkfeed = _get_gkfeed()

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
