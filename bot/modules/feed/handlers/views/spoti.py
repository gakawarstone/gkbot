from bs4 import BeautifulSoup, Tag

from services.feed_parser import feed_parser
from services.gkfeed import FeedItem
from services.http import HttpService

from . import BaseFeedItemView


class SpotiFeedItemView(BaseFeedItemView):
    async def _process_spoti_item(self, item: FeedItem) -> None:
        html = await HttpService.get(item.link)
        data = await feed_parser.run(SpotiFeedItemView._parse_spoti_page, html)
        if data is None:
            return await self._send_item(item)
        media_url, title, description = data

        if description.split(" · ")[0] == "Playlist":
            return await self._send_photo(item, media_url, "", title)

        artist_name = description.split(" · ")[0]
        release_name = title.split(" - ")[0]
        await self._send_photo(
            item,
            media_url,
            f"{release_name} - {artist_name}",
            "Spotify Release",
        )

    @staticmethod
    def _parse_spoti_page(html: bytes) -> tuple[str, str, str] | None:
        soup = BeautifulSoup(html, "html.parser")
        meta_tag = soup.find("meta", attrs={"name": "twitter:image"})
        if not isinstance(meta_tag, Tag):
            return None

        media_url = meta_tag.get("content")
        if not media_url:
            return None

        title_tag = soup.find("meta", attrs={"name": "twitter:title"})
        if not isinstance(title_tag, Tag):
            return None
        title = str(title_tag.get("content") or "")

        description_tag = soup.find("meta", attrs={"name": "twitter:description"})
        if not isinstance(description_tag, Tag):
            return None
        description = str(description_tag.get("content") or "")

        return str(media_url), title, description
