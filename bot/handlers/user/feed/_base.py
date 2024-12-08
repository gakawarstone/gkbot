from aiogram.handlers import BaseHandler as _BaseHandler
from bs4 import BeautifulSoup

from services.http import HttpService
from configs.env import GKFEED_USER, GKFEED_PASSWORD
from services.gkfeed import GkfeedService, FeedItem
from ui.keyboards.feed import FeedMarkup


class BaseHandler(_BaseHandler):
    _gkfeed = GkfeedService(GKFEED_USER, GKFEED_PASSWORD)

    async def _send_items_from_feed(self, feed_id: int, limit=10) -> None:
        items_cnt = 0
        async for item in self._gkfeed.get_items_from_feed(feed_id):
            if items_cnt > limit:
                break

            await self.event.message.answer(
                f'<a href="{item.link}">Link</a>',
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            )

            items_cnt += 1

    async def _send_item(self, item: FeedItem):
        await self.event.answer(
            f'<a href="{item.link}">Link</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    async def _get_soup(self, url: str) -> BeautifulSoup:
        html = await HttpService.get(url)
        return BeautifulSoup(html, "html.parser")
