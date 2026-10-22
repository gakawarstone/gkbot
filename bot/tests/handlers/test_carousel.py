from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import (
    CallbackQuery,
    Chat,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    User,
)

from extensions.handlers.callback.carousel import CarouselWidgetEventHandlerExtension
from ui.keyboards.carousel import (
    BaseCarouselMarkup,
    CarouselMarkupButtons,
    CarouselMarkupData,
)


class CarouselMarkup(BaseCarouselMarkup[CarouselMarkupButtons, CarouselMarkupData]):
    prefix = "test"
    buttons = CarouselMarkupButtons
    data = CarouselMarkupData

    @classmethod
    def get_item_markup(
        cls, item_id: str, media_len: int, media_current_num: int
    ) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                cls._get_carousel_navs_row(media_current_num, media_len, item_id)
            ]
        )


class CarouselHandler(CarouselWidgetEventHandlerExtension[CarouselMarkup]):
    _markup = CarouselMarkup

    async def _get_media_list(self) -> list[InputMediaPhoto]:
        return [
            InputMediaPhoto(media=f"https://example.com/{index}.jpg")
            for index in range(2)
        ]


@pytest.mark.parametrize("item_id", ["opaque-id", "0012"])
async def test_navigation_preserves_string_item_id(item_id: str) -> None:
    message = Message(
        message_id=1, date=datetime.now(UTC), chat=Chat(id=1, type="private")
    )
    callback = CallbackQuery(
        id="1",
        from_user=User(id=1, is_bot=False, first_name="Test"),
        chat_instance="test",
        message=message,
        data=f"test:pknext:0:{item_id}",
    )
    with (
        patch.object(Message, "edit_media", new_callable=AsyncMock) as edit_media,
        patch.object(
            Message, "edit_reply_markup", new_callable=AsyncMock
        ) as edit_markup,
    ):
        await CarouselHandler(callback).handle()

    assert edit_media.call_args.args[0].media == "https://example.com/1.jpg"
    markup = edit_markup.call_args.kwargs["reply_markup"]
    assert markup.inline_keyboard[0][0].callback_data == f"test:pkprev:1:{item_id}"
