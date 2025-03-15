from aiogram.types import URLInputFile, InputMediaPhoto

from services.http import HttpService
from extensions.handlers.message.http import HttpExtension
from extensions.handlers.callback.corousel import CorouselWidgetEventHandlerExtention
from ui.keyboards.feed.piokok import PiokokFeedItemMarkup
from ..._base import BaseHandler


class PiokokCorouselWidgetEventHandler(
    CorouselWidgetEventHandlerExtention,
    HttpExtension,
    BaseHandler,
):
    _markup = PiokokFeedItemMarkup

    async def _get_media_list(self) -> list[InputMediaPhoto]:
        item_id = int(await self._callback_data())
        item = await self._gkfeed.get_item_by_item_id(int(item_id))
        soup = await self._get_soup(item.link)
        return [
            InputMediaPhoto(
                media=URLInputFile(await HttpService.get_redirected_url(pic.a["href"]))
            )
            for pic in soup.find_all(class_="pic")
        ]
