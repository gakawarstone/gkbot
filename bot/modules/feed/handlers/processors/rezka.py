from urllib.parse import urlsplit, urlunsplit

from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService

from ._simple_rendering import SendItem, SendPhoto
from .registry import FeedProcessor

_PREVIEW_HEADERS = {"User-Agent": "TelegramBot (like TwitterBot)"}


def _matches_rezka(item: FeedItem) -> bool:
    return item.link.startswith("https://hdrezka.me")


def create_rezka_processor(send_photo: SendPhoto, send_item: SendItem) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        item_url = urlsplit(item.link)
        preview_url = urlunsplit(item_url._replace(netloc="rezka.ag"))
        metadata = await OpenGraphService.get(preview_url, headers=_PREVIEW_HEADERS)
        if metadata.image_url is None:
            return await send_item(item)

        await send_photo(item, metadata.image_url, item.title)

    return FeedProcessor("rezka", _matches_rezka, process)
