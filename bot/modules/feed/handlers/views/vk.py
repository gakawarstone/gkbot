from aiogram.types import InlineKeyboardMarkup
from bs4 import Tag, BeautifulSoup

from services.gkfeed import FeedItem
from extensions.handlers.message.http import HttpExtension
from ...ui.keyboards import FeedMarkup
from . import BaseFeedItemView
from ...ui.keyboards.vk import VKFeedVideoItemMarkup

_DEFAULT_THUMBNAIL_URL = (
    "http://sun6-21.userapi.com/fafvjSB8ha2EWPn-VR6LIahBtBkf50LZSLbKfQ/BiN2pjgeJTw.png"
)


class VKFeedItemView(BaseFeedItemView, HttpExtension):
    async def _process_vk_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        image_meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(image_meta_tag, Tag):
            return await self._send_text_item(item, soup)

        media_url = image_meta_tag.get("content")
        if not media_url or media_url == _DEFAULT_THUMBNAIL_URL:
            return await self._send_text_item(item, soup)

        reply_markup: InlineKeyboardMarkup | None = None
        video_meta_tag = soup.find("meta", attrs={"property": "og:video"})
        if video_meta_tag and isinstance(video_meta_tag, Tag):
            object_id = video_meta_tag.get("content").split("oid=")[-1].split("&")[0]
            video_id = video_meta_tag.get("content").split("id=")[-1].split("&")[0]
            video_link = f"https://vk.com/video{object_id}_{video_id}"
            reply_markup = VKFeedVideoItemMarkup.get_item_markup(item.id, video_link)

        title_tag = soup.find("title")
        title = title_tag.text if isinstance(title_tag, Tag) else ""

        await self._send_photo(
            item,
            str(media_url),
            title.split(" | ")[0],
            title.split(" | ")[1],
            reply_markup,
        )

    async def _send_text_item(self, item: FeedItem, soup: BeautifulSoup):
        soup = await self._get_soup(item.link)

        description_tag = soup.find("meta", attrs={"property": "og:description"})
        if not description_tag or not isinstance(description_tag, Tag):
            raise ValueError("Description meta tag not found")

        description = description_tag.get("content")
        if not description or not isinstance(description, str):
            raise ValueError("Description content not found")

        await self.answer(
            f"<b>{description.replace('<br>', '\n')}</b>\n\n<a href='{item.link}'>{self._get_channel_name(soup)}</a>",
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            disable_web_page_preview=True,
        )

    def _get_channel_name(self, soup: BeautifulSoup) -> str:
        title_tag = soup.find("title")
        title = title_tag.text if isinstance(title_tag, Tag) else ""
        return title.split(" | ")[1]
