from typing import Any, Type
from abc import abstractmethod

from aiogram.types import InputMediaPhoto, Message

from ui.keyboards.carousel import BaseCarouselMarkup
from .base import BaseHandler


class CarouselWidgetEventHandlerExtension[T: BaseCarouselMarkup](BaseHandler):
    _markup: Type[T]

    async def _parse_callback(self) -> tuple[str, int, str]:
        if not self.event.data:
            raise ValueError("No callback data provided")

        prefix, event, current_media_num, data = self.event.data.split(":")

        if prefix != self._markup.prefix:
            raise ValueError("Wrong Handler configuration prefix isn't same")

        return event, int(current_media_num), data

    async def _callback_data(self) -> str:
        _, _, data = await self._parse_callback()
        return data

    @abstractmethod
    async def _get_media_list(self) -> list[InputMediaPhoto]:
        pass

    async def handle(self) -> Any:
        event, media_current_num, data = await self._parse_callback()
        if event == self._markup.data.show_next_media:
            media_current_num += 1

        if event == self._markup.data.show_prev_media:
            media_current_num -= 1

        media = await self._get_media_list()
        media_link = media[media_current_num]

        await self._update_widget(data, media_link, len(media), media_current_num)

    async def _update_widget(
        self,
        data: str,
        media: InputMediaPhoto,
        media_len: int,
        media_current_num: int,
    ):
        if not self.event.message:
            raise ValueError("No message to edit")

        if not isinstance(self.event.message, Message):
            raise ValueError("Callback message is not of type Message")

        message = self.event.message
        await message.edit_media(media)
        # await message.edit_caption(caption=f'<a href="{item.link}">Link</a>')
        # Get the get_item_markup method from the concrete implementation
        get_item_markup = getattr(self._markup, "get_item_markup")
        await message.edit_reply_markup(
            reply_markup=get_item_markup(
                int(data),  # FIXME: str instead of int
                media_len,
                media_current_num,
            )
        )
