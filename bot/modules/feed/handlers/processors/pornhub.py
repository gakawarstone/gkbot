from modules.feed.ui.keyboards.pornhub import PornhubFeedItemMarkup
from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService

from .registry import FeedProcessor
from .rendering import FeedRendering


def create_pornhub_processor(rendering: FeedRendering) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None:
            return await rendering.send_item(item)

        title = metadata.title or item.title
        parts = title.split(" - ")
        link_caption = parts[-1]

        await rendering.send_photo(
            item,
            metadata.image_url,
            parts[0],
            link_caption=link_caption,
            reply_markup=PornhubFeedItemMarkup.get_item_markup(item.id, item.link),
            has_spoiler=True,
        )

    return FeedProcessor(
        "pornhub",
        lambda item: item.link.startswith(
            ("https://www.pornhub.com", "https://de.pornhub.org", "https://pornhub.org")
        ),
        process,
    )
