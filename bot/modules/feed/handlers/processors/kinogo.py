from bs4 import Tag

from services.gkfeed import FeedItem

from ._simple_rendering import SendItem, SendPhoto, get_html_soup
from .registry import FeedProcessor


def _matches_kinogo(item: FeedItem) -> bool:
    return item.link.startswith("https://kinogo")


def create_kinogo_processor(
    send_photo: SendPhoto, send_item: SendItem
) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        soup = await get_html_soup(item.link)
        link = soup.find("link")
        if not isinstance(link, Tag):
            return await send_item(item)

        media_url = link.get("href")
        if not media_url:
            return await send_item(item)

        await send_photo(item, str(media_url), "")

    return FeedProcessor("kinogo", _matches_kinogo, process)
