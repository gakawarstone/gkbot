from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData
from ..url_button import UrlButton


class RedditFeedItemMarkup(
    BaseFeedMarkup[FeedMarkupButtons, FeedMarkupData],
):
    prefix = "fdreddit"
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, link: str):
        return InlineKeyboardBuilder(
            [
                [
                    UrlButton.create(link, "Читать"),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
