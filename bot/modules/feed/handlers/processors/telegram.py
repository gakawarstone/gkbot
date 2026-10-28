from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService

from ._simple_rendering import SendItem, SendPhoto
from .registry import FeedProcessor


def _matches_telegram(item: FeedItem) -> bool:
    return item.link.startswith("https://t.me")


def create_telegram_processor(
    send_photo: SendPhoto, send_item: SendItem
) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None or metadata.description is None:
            return await send_item(item)

        description = metadata.description
        if len(description) > 250:
            description = description[:247] + "..."
        await send_photo(item, metadata.image_url, description)

    return FeedProcessor("telegram", _matches_telegram, process)
