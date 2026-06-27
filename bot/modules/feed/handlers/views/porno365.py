from bs4 import Tag

from services.gkfeed import FeedItem
from modules.feed.handlers.views.base import BaseWebFeedItemView
from modules.feed.ui.keyboards.porno365 import Porno365FeedItemMarkup


class Porno365FeedItemView(BaseWebFeedItemView):
    async def _process_porno365_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(meta_tag, Tag):
            return await self._send_item(item)

        media_url = meta_tag.get("content")
        if not media_url:
            return await self._send_item(item)

        title_tag = soup.find("title")
        title = title_tag.text if isinstance(title_tag, Tag) else ""

        await self._send_photo(
            item,
            str(media_url),
            title,
            link_caption="porno365",
            reply_markup=Porno365FeedItemMarkup.get_item_markup(item.id, item.link),
        )
