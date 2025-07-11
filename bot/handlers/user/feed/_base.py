from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery

from configs.env import GKFEED_USER, GKFEED_PASSWORD
from services.gkfeed import GkfeedService, FeedItem
from ui.keyboards.feed import FeedMarkup


class BaseHandler(_BaseHandler):
    _gkfeed = GkfeedService(GKFEED_USER, GKFEED_PASSWORD)

    async def _send_item(self, item: FeedItem):
        await self.bot.send_message(
            self.event.from_user.id,
            f'<a href="{item.link}">Link</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    async def answer(self, *args, **kwargs):
        if isinstance(self.event, CallbackQuery):
            return await self.event.message.answer(*args, **kwargs)
        return await self.event.answer(*args, **kwargs)
