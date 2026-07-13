import json
from datetime import datetime
from html import escape

from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, Tag

from services.gkfeed import FeedItem
from services.http import HttpService

from ...ui.keyboards import FeedMarkup

from . import BaseFeedItemView

_PREVIEW_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Twitterbot/1.0)"}


class HltvFeedItemView(BaseFeedItemView):
    async def _process_hltv_item(self, item: FeedItem) -> None:
        soup = await self._get_hltv_soup(item.link)

        image_tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(image_tag, Tag):
            return await self._send_item(item)

        image_url = image_tag.get("content")
        if not isinstance(image_url, str) or not image_url:
            return await self._send_item(item)

        matchup, match_time = self._get_match_details(soup, item.title)

        image_data = await HttpService.get(self._normalize_image_url(image_url))
        photo = BufferedInputFile(image_data, filename="hltv.png")

        await self.answer_photo(
            photo,
            caption=self._get_caption(item.link, matchup, match_time),
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    async def _get_hltv_soup(self, url: str) -> BeautifulSoup:
        html = await HttpService.get_with_downloader(url, headers=_PREVIEW_HEADERS)
        return BeautifulSoup(html, "html.parser")

    @staticmethod
    def _normalize_image_url(image_url: str) -> str:
        if image_url.startswith("http://"):
            return f"https://{image_url.removeprefix('http://')}"
        return image_url

    @staticmethod
    def _get_match_details(
        soup: BeautifulSoup, fallback_title: str
    ) -> tuple[str, str | None]:
        title_tag = soup.find("meta", attrs={"property": "og:title"})
        title = title_tag.get("content") if isinstance(title_tag, Tag) else None
        if not isinstance(title, str) or not title:
            title = fallback_title
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
