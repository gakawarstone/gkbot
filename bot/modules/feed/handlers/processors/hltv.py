import json
from datetime import datetime
from html import escape

from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, Tag

from services.gkfeed import FeedItem
from services.http import HttpService
from services.open_graph import OpenGraphService

from ...ui.keyboards import FeedMarkup
from ._simple_rendering import AnswerBufferedPhoto, SendItem
from .registry import FeedProcessor


def _matches_hltv(item: FeedItem) -> bool:
    return item.link.startswith("https://www.hltv.org")


def create_hltv_processor(
    answer_photo: AnswerBufferedPhoto, send_item: SendItem
) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        soup = await OpenGraphService.get_soup(item.link, use_downloader=True)
        metadata = OpenGraphService.parse_soup(soup)
        if metadata.image_url is None:
            return await send_item(item)

        matchup, match_time = _get_match_details(soup, metadata.title or item.title)
        image_data = await HttpService.get(_normalize_image_url(metadata.image_url))
        photo = BufferedInputFile(image_data, filename="hltv.png")
        await answer_photo(
            photo,
            caption=_get_caption(item.link, matchup, match_time),
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    return FeedProcessor("hltv", _matches_hltv, process)


def _normalize_image_url(image_url: str) -> str:
    if image_url.startswith("http://"):
        return f"https://{image_url.removeprefix('http://')}"
    return image_url


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


def _get_caption(link: str, matchup: str, match_time: str | None) -> str:
    matchup_link = f'<a href="{escape(link, quote=True)}">{escape(matchup)}</a>'
    if match_time is None:
        return matchup_link
    return f"<b>{escape(match_time)}</b>\n\n{matchup_link}"
