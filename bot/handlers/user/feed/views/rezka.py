from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from ui.keyboards.feed import FeedMarkup
from . import BaseFeedItemView


class RezkaFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_rezka_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not meta_tag:
            await self.answer(
                f'<a href="{item.link}">Link</a>',
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            )
            return

        media_url = meta_tag["content"]
        await self._send_photo(item, media_url, item.title)
        return
