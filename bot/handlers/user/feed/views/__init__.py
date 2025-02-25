from aiogram.types import URLInputFile

from services.gkfeed import FeedItem
from ui.keyboards.feed import FeedMarkup
from .._base import BaseHandler


class BaseFeedItemView(BaseHandler):
    async def _send_photo(
        self,
        item: FeedItem,
        media_url: str,
        description: str,
        link_caption: str = "Link",
    ):
        await self.bot.send_photo(
            self.event.from_user.id,
            URLInputFile(media_url),
            caption=f'<b>{description}</b>\n\n<a href="{item.link}">{link_caption}</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )
