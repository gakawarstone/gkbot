from aiogram.types import DisabledButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

_PREFIX = "fd"


class FeedMarkupButtons:
    delete = "Убрать"
    keep = "Оставить"
    similar = "Похожие"


class FeedMarkupData:
    delete = "del"
    keep = "keep"


class BaseFeedMarkup[T: FeedMarkupButtons, S: FeedMarkupData]:
    prefix: str
    buttons: type[T]
    data: type[S]

    # NOTE: do not support custom handler for feed row
    #       it would be handled with handler associated with FeedMarkup
    @classmethod
    def _get_feed_buttons_row(cls, item_id: int) -> list[InlineKeyboardButton]:
        return [
            InlineKeyboardButton(
                text=cls.buttons.keep,
                callback_data=f"{_PREFIX}:{cls.data.keep}:{item_id}",
            ),
            InlineKeyboardButton(
                text=cls.buttons.delete,
                callback_data=f"{_PREFIX}:{cls.data.delete}:{item_id}",
            ),
        ]


class FeedMarkup(BaseFeedMarkup[FeedMarkupButtons, FeedMarkupData]):
    prefix = _PREFIX
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, feed_id: int) -> InlineKeyboardMarkup:
        """Build item actions, retaining feed_id for compatibility with callers."""
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=cls.buttons.similar,
                        disabled=DisabledButton(),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
