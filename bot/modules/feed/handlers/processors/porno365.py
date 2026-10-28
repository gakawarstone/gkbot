from modules.feed.ui.keyboards.porno365 import Porno365FeedItemMarkup
from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService

from .registry import FeedProcessor
from .rendering import FeedRendering


def create_porno365_processor(rendering: FeedRendering) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None:
            return await rendering.send_item(item)

        await rendering.send_photo(
            item,
            metadata.image_url,
            metadata.title or item.title,
            link_caption="porno365",
            reply_markup=Porno365FeedItemMarkup.get_item_markup(item.id, item.link),
            has_spoiler=True,
        )

    return FeedProcessor(
        "porno365",
        lambda item: item.link.startswith(("http://porno365.broker",)),
        process,
    )
