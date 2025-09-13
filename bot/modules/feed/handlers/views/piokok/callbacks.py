from aiogram.types import URLInputFile, InputMediaPhoto

from services.http import HttpService
from extensions.handlers.message.http import HttpExtension
from extensions.handlers.callback.carousel import CarouselWidgetEventHandlerExtension
from ....ui.keyboards.piokok import PiokokFeedItemMarkup
from bs4 import Tag
from ..._base import BaseHandler


class PiokokCarouselWidgetEventHandler(
    CarouselWidgetEventHandlerExtension,
    HttpExtension,
    BaseHandler,
):
    _markup = PiokokFeedItemMarkup

    async def _get_media_list(self) -> list[InputMediaPhoto]:
        item_id = int(await self._callback_data())
        item = await (await self._gkfeed()).get_item_by_item_id(int(item_id))
        soup = await self._get_soup(item.link)
        photos: list[InputMediaPhoto] = []
        for pic in soup.find_all(class_="pic"):
            if isinstance(pic, Tag) and pic.a and pic.a.get("href"):
                redirected = await HttpService.get_redirected_url(str(pic.a.get("href")))
                photos.append(InputMediaPhoto(media=URLInputFile(redirected)))
        return photos
