from aiogram.types import InlineKeyboardMarkup
from bs4 import BeautifulSoup, Tag

from services.feed_parser import feed_parser
from services.gkfeed import FeedItem
from services.open_graph import OpenGraphMetadata, OpenGraphService

from ...ui.keyboards import FeedMarkup
from ...ui.keyboards.vk import VKFeedVideoItemMarkup
from . import BaseFeedItemView

_DEFAULT_THUMBNAIL_URL = (
    "http://sun6-21.userapi.com/fafvjSB8ha2EWPn-VR6LIahBtBkf50LZSLbKfQ/BiN2pjgeJTw.png"
)


class VKFeedItemView(BaseFeedItemView):
    async def _process_vk_item(self, item: FeedItem) -> None:
        html = await OpenGraphService.get_html(item.link)
        metadata, title, channel_name = await feed_parser.run(
            VKFeedItemView._parse_vk_page, html
        )

        if not self._is_media_item(metadata):
            return await self._send_text_item(item, channel_name, metadata)

        media_url = self._get_image(metadata)
        reply_markup = None
        if self._is_video_item(metadata):
            reply_markup = self._get_video_markup(item, metadata)

        await self._send_photo(
            item=item,
            media_url=media_url,
            description=title,
            link_caption=channel_name,
            reply_markup=reply_markup,
        )

    async def _send_text_item(
        self,
        item: FeedItem,
        channel_name: str,
        metadata: OpenGraphMetadata,
    ) -> None:
        description = self._get_description(metadata)
        await self.answer(
            f"<b>{description.replace('<br>', '\n')}</b>\n\n<a href='{item.link}'>{channel_name}</a>",
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            disable_web_page_preview=True,
        )

    def _is_media_item(self, metadata: OpenGraphMetadata) -> bool:
        return (
            metadata.image_url is not None
            and metadata.image_url != _DEFAULT_THUMBNAIL_URL
        )

    def _is_video_item(self, metadata: OpenGraphMetadata) -> bool:
        player_url = metadata.video_url
        return (
            player_url is not None
            and "oid=" in player_url
            and "&" in player_url
            and "id=" in player_url
        )

    def _get_image(self, metadata: OpenGraphMetadata) -> str:
        if metadata.image_url is None:
            raise ValueError("VK preview image meta tag not found")
        return metadata.image_url

    def _get_description(self, metadata: OpenGraphMetadata) -> str:
        if metadata.description is None:
            raise ValueError("VK description meta tag not found")
        return metadata.description

    @classmethod
    def _parse_vk_page(cls, html: bytes) -> tuple[OpenGraphMetadata, str, str]:
        soup = BeautifulSoup(html, "html.parser")
        metadata = OpenGraphService.parse_soup(soup)
        title, channel_name = cls._parse_title(soup)
        return metadata, title, channel_name

    @staticmethod
    def _parse_title(soup: BeautifulSoup) -> tuple[str, str]:
        tag = soup.find("title")
        if not isinstance(tag, Tag):
            raise ValueError("title tag not found")  # noqa: TRY004

        raw_title = tag.text
        parts = raw_title.split(" | ")
        if len(parts) < 2:
            return raw_title, ""

        return parts[0], parts[1]

    def _get_video_markup(
        self,
        item: FeedItem,
        metadata: OpenGraphMetadata,
    ) -> InlineKeyboardMarkup:
        content = metadata.video_url
        if content is None:
            raise ValueError("VK video player meta tag not found")

        oid_part = content.split("oid=")[-1].split("&")[0]
        id_part = content.split("id=")[-1].split("&")[0]

        video_link = f"https://vk.com/video{oid_part}_{id_part}"
        return VKFeedVideoItemMarkup.get_item_markup(item.id, video_link)
