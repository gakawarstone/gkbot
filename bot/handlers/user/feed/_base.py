from aiogram.handlers import BaseHandler as _BaseHandler

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
