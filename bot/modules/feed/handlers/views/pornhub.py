from modules.feed.handlers.views.base import BaseWebFeedItemView
from modules.feed.ui.keyboards.pornhub import PornhubFeedItemMarkup
from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService


class PornhubFeedItemView(BaseWebFeedItemView):
    async def _process_pornhub_item(self, item: FeedItem) -> None:
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None:
            return await self._send_item(item)

        title = metadata.title or item.title
        parts = title.split(" - ")
        link_caption = parts[-1]

        await self._send_photo(
            item,
            metadata.image_url,
            parts[0],
            link_caption=link_caption,
            reply_markup=PornhubFeedItemMarkup.get_item_markup(item.id, item.link),
            has_spoiler=True,
        )
