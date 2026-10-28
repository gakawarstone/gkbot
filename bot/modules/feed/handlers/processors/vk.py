from bs4 import BeautifulSoup, Tag

from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService

from ...ui.keyboards import FeedMarkup
from ...ui.keyboards.vk import VKFeedVideoItemMarkup
from .._exceptions import FeedMediaExtractionError
from .registry import FeedProcessor
from .rendering import FeedRendering

_DEFAULT_THUMBNAIL_URL = (
    "http://sun6-21.userapi.com/fafvjSB8ha2EWPn-VR6LIahBtBkf50LZSLbKfQ/BiN2pjgeJTw.png"
)


def create_vk_processor(rendering: FeedRendering) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        soup = await OpenGraphService.get_soup(item.link)
        metadata = OpenGraphService.parse_soup(soup)
        image_url = metadata.image_url

        if image_url is None or image_url == _DEFAULT_THUMBNAIL_URL:
            if metadata.description is None:
                raise FeedMediaExtractionError("VK description meta tag not found")
            _, channel_name = _parse_title(soup)
            description = metadata.description.replace("<br>", "\n")
            await rendering.answer(
                f"<b>{description}</b>\n\n<a href='{item.link}'>{channel_name}</a>",
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
                disable_web_page_preview=True,
            )
            return

        title, channel_name = _parse_title(soup)
        reply_markup = None
        player_url = metadata.video_url
        if (
            player_url is not None
            and "oid=" in player_url
            and "&" in player_url
            and "id=" in player_url
        ):
            owner_id = player_url.split("oid=")[-1].split("&")[0]
            video_id = player_url.split("id=")[-1].split("&")[0]
            reply_markup = VKFeedVideoItemMarkup.get_item_markup(
                item.id, f"https://vk.com/video{owner_id}_{video_id}"
            )

        await rendering.send_photo(
            item=item,
            media_url=image_url,
            description=title,
            link_caption=channel_name,
            reply_markup=reply_markup,
        )

    return FeedProcessor(
        "vk",
        lambda item: item.link.startswith(("https://vk",)),
        process,
    )


def _parse_title(soup: BeautifulSoup) -> tuple[str, str]:
    tag = soup.find("title")
    if not isinstance(tag, Tag):
        raise FeedMediaExtractionError("title tag not found")

    parts = tag.text.split(" | ")
    if len(parts) < 2:
        return tag.text, ""
    return parts[0], parts[1]
