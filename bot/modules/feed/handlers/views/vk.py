from aiogram.types import InlineKeyboardMarkup
from bs4 import Tag, BeautifulSoup

from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from ...ui.keyboards import FeedMarkup
from ...ui.keyboards.vk import VKFeedVideoItemMarkup
from . import BaseFeedItemView

_DEFAULT_THUMBNAIL_URL = (
    "http://sun6-21.userapi.com/fafvjSB8ha2EWPn-VR6LIahBtBkf50LZSLbKfQ/BiN2pjgeJTw.png"
)


class VKFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_vk_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        if not self._is_media_item(soup):
            return await self._send_text_item(item, soup)

        media_url = self._get_og_image(soup)
        title, channel_name = self._parse_title(soup)

        reply_markup = None
        if self._is_video_item(soup):
            reply_markup = self._get_video_markup(item, soup)

        await self._send_photo(
            item=item,
            media_url=media_url,
            description=title,
            link_caption=channel_name,
            reply_markup=reply_markup,
        )

    async def _send_text_item(self, item: FeedItem, soup: BeautifulSoup):
        description = self._get_og_description(soup)
        _, channel_name = self._parse_title(soup)

        await self.answer(
            f"<b>{description.replace('<br>', '\n')}</b>\n\n<a href='{item.link}'>{channel_name}</a>",
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            disable_web_page_preview=True,
        )

    def _is_media_item(self, soup: BeautifulSoup) -> bool:
        tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(tag, Tag):
            return False

        content = tag.get("content")
        if not isinstance(content, str) or not content or content == _DEFAULT_THUMBNAIL_URL:
            return False

        return True

    def _is_video_item(self, soup: BeautifulSoup) -> bool:
        tag = soup.find("meta", attrs={"property": "og:video"})
        if not isinstance(tag, Tag):
            return False

        content = tag.get("content")
        if not isinstance(content, str):
            return False

        return "oid=" in content and "&" in content and "id=" in content

    def _get_og_image(self, soup: BeautifulSoup) -> str:
        tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(tag, Tag):
            raise ValueError("og:image meta tag not found")

        content = tag.get("content")
        if not isinstance(content, str):
            raise ValueError("og:image content not found")

        return content

    def _get_og_description(self, soup: BeautifulSoup) -> str:
        tag = soup.find("meta", attrs={"property": "og:description"})
        if not isinstance(tag, Tag):
            raise ValueError("og:description meta tag not found")

        content = tag.get("content")
        if not isinstance(content, str):
            raise ValueError("og:description content not found")

        return content

    def _parse_title(self, soup: BeautifulSoup) -> tuple[str, str]:
        tag = soup.find("title")
        if not isinstance(tag, Tag):
            raise ValueError("title tag not found")

        raw_title = tag.text
        parts = raw_title.split(" | ")
        if len(parts) < 2:
            return raw_title, ""

        return parts[0], parts[1]

    def _get_video_markup(
        self,
        item: FeedItem,
        soup: BeautifulSoup,
    ) -> InlineKeyboardMarkup:
        tag = soup.find("meta", attrs={"property": "og:video"})
        if not isinstance(tag, Tag):
            raise ValueError("og:video meta tag not found")

        content = tag.get("content")
        if not isinstance(content, str):
            raise ValueError("og:video content not found")

        oid_part = content.split("oid=")[-1].split("&")[0]
        id_part = content.split("id=")[-1].split("&")[0]

        video_link = f"https://vk.com/video{oid_part}_{id_part}"
        return VKFeedVideoItemMarkup.get_item_markup(item.id, video_link)

