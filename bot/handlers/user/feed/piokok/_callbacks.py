from typing import Any

from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery, URLInputFile, InputMediaPhoto

from services.gkfeed import FeedItem
from ui.keyboards.feed.piokok import PiokokFeedMarkup
from .._base import BaseHandler


class PiokokCorouselWidgetEventHandler(BaseHandler, _BaseHandler[CallbackQuery]):
    async def _parse_callback(self) -> tuple[str, str]:
        if not self.event.data:
            raise ValueError("No callback data providet")

        _, event, data = self.event.data.split(":")
        return event, data

    async def handle(self) -> Any:
        event, data = await self._parse_callback()
        item_id, media_current_num = data.split("_")
        item = await self._gkfeed.get_item_by_item_id(int(item_id))
        media_current_num = int(media_current_num)

        if event == PiokokFeedMarkup.data.show_next_media:
            media_current_num += 1

        if event == PiokokFeedMarkup.data.show_prev_media:
            media_current_num -= 1

        soup = await self._get_soup(item.link)
        photos = [pic.a["href"] for pic in soup.find_all(class_="pic")]
        media_link = photos[int(media_current_num)]
        await self._update_widget(item, media_link, len(photos), media_current_num)

    async def _update_widget(
        self, item: FeedItem, media_link: str, media_len: int, media_current_num: int
    ):
        if not self.event.message:
            raise ValueError("No message to edit")

        await self.event.message.edit_media(
            InputMediaPhoto(media=URLInputFile(media_link))
        )
        await self.event.message.edit_caption(caption=f'<a href="{item.link}">Link</a>')
        await self.event.message.edit_reply_markup(
            reply_markup=PiokokFeedMarkup.get_item_markup(
                item.id, media_len, media_current_num
            )
        )
