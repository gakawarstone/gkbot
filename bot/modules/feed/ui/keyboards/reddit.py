from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData
from ui.keyboards.url_button import UrlButton


class RedditFeedItemMarkup(
    BaseFeedMarkup[FeedMarkupButtons, FeedMarkupData],
):
    prefix = "fdreddit"
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, link: str, link_caption: str = "Читать"):
        return InlineKeyboardBuilder(
            [
                [
                    UrlButton.create(link, link_caption),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
