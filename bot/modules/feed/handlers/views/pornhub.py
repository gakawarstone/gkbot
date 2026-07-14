from aiogram.exceptions import TelegramBadRequest
from aiogram.types import URLInputFile

from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService
from modules.feed.ui.keyboards.pornhub import PornhubFeedItemMarkup
from modules.feed.handlers.views.base import BaseWebFeedItemView


class PornhubFeedItemView(BaseWebFeedItemView):
    async def _process_pornhub_item(self, item: FeedItem):
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None:
            return await self._send_item(item)

        title = metadata.title or item.title
        parts = title.split(" - ")
        link_caption = parts[-1]

        await self.__send_photo(
            item,
            metadata.image_url,
            parts[0],
            link_caption=link_caption,
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
                reply_markup=PornhubFeedItemMarkup.get_item_markup(item.id, item.link),
                has_spoiler=True,
            )
        except TelegramBadRequest:
            await self._send_item(item)
