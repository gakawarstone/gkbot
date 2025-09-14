from urllib.parse import parse_qs, urlparse

from aiogram.utils.keyboard import InlineKeyboardBuilder

from ui.buttons.pornhub.download import (
    PornhubDownloadButtonBuilder,
    PornhubDownloadButtonCallbackData,
    PornhubDownloadButtonData,
)
from . import BaseFeedMarkup, FeedMarkupButtons, FeedMarkupData


class PornhubFeedItemMarkup(BaseFeedMarkup):
    buttons = FeedMarkupButtons
    data = FeedMarkupData

    @classmethod
    def get_item_markup(cls, item_id: int, link: str):
        parsed_url = urlparse(link)
        query_params = parse_qs(parsed_url.query)
        viewkey = query_params.get("viewkey", [None])[0]

        if not viewkey:
            return InlineKeyboardBuilder(
                [
                    cls._get_feed_buttons_row(item_id),
                ]
            ).as_markup()

        return InlineKeyboardBuilder(
            [
                [
                    PornhubDownloadButtonBuilder.build(
                        PornhubDownloadButtonData.video,
                        PornhubDownloadButtonCallbackData(viewkey),
                    ),
                ],
                cls._get_feed_buttons_row(item_id),
            ]
        ).as_markup()
