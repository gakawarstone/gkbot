import json
from datetime import datetime
from html import escape

from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, Tag

from services.feed_parser import FeedParser
from services.gkfeed import FeedItem
from services.http import HttpService
from services.open_graph import OpenGraphMetadata, OpenGraphService

from ...ui.keyboards import FeedMarkup
from . import BaseFeedItemView


class HltvFeedItemView(BaseFeedItemView):
    async def _process_hltv_item(self, item: FeedItem) -> None:
        html = await OpenGraphService.get_html(item.link, use_downloader=True)
        metadata, matchup, match_time = await FeedParser.run(
            HltvFeedItemView._parse_hltv_page, html, item.title
        )

        if metadata.image_url is None:
            return await self._send_item(item)

        image_data = await HttpService.get(
            self._normalize_image_url(metadata.image_url)
        )
        photo = BufferedInputFile(image_data, filename="hltv.png")

        await self.answer_photo(
            photo,
            caption=self._get_caption(item.link, matchup, match_time),
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    @classmethod
    def _parse_hltv_page(
        cls, html: bytes, title: str
    ) -> tuple[OpenGraphMetadata, str, str | None]:
        soup = BeautifulSoup(html, "html.parser")
        metadata = OpenGraphService.parse_soup(soup)
        matchup, match_time = cls._get_match_details(soup, metadata.title or title)
        return metadata, matchup, match_time

    @staticmethod
    def _normalize_image_url(image_url: str) -> str:
        if image_url.startswith("http://"):
            return f"https://{image_url.removeprefix('http://')}"
        return image_url

    @staticmethod
    def _get_match_details(
        soup: BeautifulSoup,
        title: str,
    ) -> tuple[str, str | None]:
        matchup = title.split(" at ", maxsplit=1)[0]

        event_tag = soup.find("script", attrs={"type": "application/ld+json"})
        if not isinstance(event_tag, Tag):
            return matchup, None

        try:
            event_data = json.loads(event_tag.get_text())
            start_date = event_data.get("startDate")
            if not isinstance(start_date, str):
                return matchup, None
            match_time = datetime.fromisoformat(start_date)
        except (json.JSONDecodeError, TypeError, ValueError):
            return matchup, None

        return matchup, f"{match_time:%d.%m.%Y %H:%M}"

    @staticmethod
    def _get_caption(link: str, matchup: str, match_time: str | None) -> str:
        matchup_link = f'<a href="{escape(link, quote=True)}">{escape(matchup)}</a>'
        if match_time is None:
            return matchup_link
        return f"<b>{escape(match_time)}</b>\n\n{matchup_link}"
