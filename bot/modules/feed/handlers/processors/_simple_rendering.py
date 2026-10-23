from collections.abc import Awaitable, Callable
from typing import Protocol

from aiogram.types import BufferedInputFile, InlineKeyboardMarkup
from bs4 import BeautifulSoup

from services.gkfeed import FeedItem
from services.http import HttpService

SendItem = Callable[[FeedItem], Awaitable[None]]


class SendPhoto(Protocol):
    def __call__(
        self,
        item: FeedItem,
        media_url: str,
        description: str,
        link_caption: str = "Link",
    ) -> Awaitable[None]: ...


class AnswerBufferedPhoto(Protocol):
    def __call__(
        self,
        photo: BufferedInputFile,
        *,
        caption: str,
        reply_markup: InlineKeyboardMarkup,
    ) -> Awaitable[object]: ...


async def get_html_soup(url: str) -> BeautifulSoup:
    html = await HttpService.get(url, headers=HttpService.headers)
    return BeautifulSoup(html, "html.parser")
