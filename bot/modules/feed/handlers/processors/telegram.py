from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService

from ._simple_rendering import SendItem, SendPhoto
from .matching import matches_source_url
from .registry import FeedProcessor


def _matches_telegram(item: FeedItem) -> bool:
    return matches_source_url(item, frozenset({"t.me"}))


def _limit_description(description: str, limit: int = 250) -> str:
    if len(description) > limit:
        return description[: limit - 3] + "..."
    return description


def create_telegram_processor(
    send_photo: SendPhoto, send_item: SendItem
) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None or metadata.description is None:
            return await send_item(item)

        await send_photo(
            item, metadata.image_url, _limit_description(metadata.description)
        )

    return FeedProcessor("telegram", _matches_telegram, process)
