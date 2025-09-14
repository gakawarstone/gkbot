from aiogram.exceptions import TelegramBadRequest
from aiogram.types import URLInputFile
from bs4 import Tag

from services.gkfeed import FeedItem
from modules.feed.ui.keyboards import FeedMarkup
from modules.feed.handlers.views.base import BaseWebFeedItemView


class PornhubFeedItemView(BaseWebFeedItemView):
    async def _process_pornhub_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        meta_tag = soup.find("meta", attrs={"property": "og:image"})
        if not isinstance(meta_tag, Tag):
            return await self._send_item(item)

        media_url = meta_tag.get("content")
        if not media_url:
            return await self._send_item(item)

        title_tag = soup.find("meta", attrs={"property": "og:title"})
        title = title_tag.get("content") if isinstance(title_tag, Tag) else ""
        if not isinstance(title, str):
            title = str(title)

        parts = title.split(" - ")
        link_caption = parts[-1]

        await self.__send_photo(
            item, str(media_url), str(parts[0]), link_caption=link_caption
        )

    async def __send_photo(
        self,
        item: FeedItem,
        media_url: str,
        description: str,
        link_caption: str = "Pornhub",
    ):
        try:
            await self.answer_photo(
                URLInputFile(media_url),
                caption=f'<b>{description}</b>\n\n<a href="{item.link}">{link_caption}</a>',
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
                has_spoiler=True,
            )
        except TelegramBadRequest:
            await self._send_item(item)
