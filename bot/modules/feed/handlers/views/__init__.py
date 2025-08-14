from aiogram.types import CallbackQuery, Message, URLInputFile
from aiogram.exceptions import TelegramBadRequest

from services.gkfeed import FeedItem
from ...ui.keyboards import FeedMarkup
from .._base import BaseHandler


class BaseFeedItemView(BaseHandler):
    event: Message | CallbackQuery

    async def _send_photo(
        self,
        item: FeedItem,
        media_url: str,
        description: str,
        link_caption: str = "Link",
    ):
        try:
            await self.answer_photo(
                URLInputFile(media_url),
                caption=f'<b>{description}</b>\n\n<a href="{item.link}">{link_caption}</a>',
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            )
        except TelegramBadRequest:
            await self._send_item(item)
