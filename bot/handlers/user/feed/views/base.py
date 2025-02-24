from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from ui.keyboards.feed import FeedMarkup
from . import BaseFeedItemView


class BaseWebFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_base_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not meta_tag:
            await self.event.answer(
                f'<a href="{item.link}">Link</a>',
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            )
            return

        media_url = meta_tag["content"]
        title = soup.find("title").text
        await self._send_photo(item, media_url, title)
        return
