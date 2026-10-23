from bs4 import Tag

from services.gkfeed import FeedItem

from ._simple_rendering import SendItem, SendPhoto, get_html_soup
from .registry import FeedProcessor


def _matches_spoti(item: FeedItem) -> bool:
    return item.link.startswith("https://open")


def create_spoti_processor(send_photo: SendPhoto, send_item: SendItem) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        soup = await get_html_soup(item.link)

        meta_tag = soup.find("meta", attrs={"name": "twitter:image"})
        if not isinstance(meta_tag, Tag):
            return await send_item(item)

        media_url = meta_tag.get("content")
        if not media_url:
            return await send_item(item)

        title_tag = soup.find("meta", attrs={"name": "twitter:title"})
        if not isinstance(title_tag, Tag):
            return await send_item(item)
        title = str(title_tag.get("content") or "")

        description_tag = soup.find("meta", attrs={"name": "twitter:description"})
        if not isinstance(description_tag, Tag):
            return await send_item(item)
        description = str(description_tag.get("content") or "")

        if description.split(" · ")[0] == "Playlist":
            return await send_photo(item, str(media_url), "", title)

        artist_name = description.split(" · ")[0]
        release_name = title.split(" - ")[0]
        await send_photo(
            item,
            str(media_url),
            f"{release_name} - {artist_name}",
            "Spotify Release",
        )

    return FeedProcessor("spoti", _matches_spoti, process)
