from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from aiogram.types import InlineKeyboardMarkup

from services.gkfeed import FeedItem


class SendPhoto(Protocol):
    def __call__(
        self,
        item: FeedItem,
        media_url: str,
        description: str,
        link_caption: str = "Link",
        reply_markup: InlineKeyboardMarkup | None = None,
        has_spoiler: bool = False,
    ) -> Awaitable[None]: ...


@dataclass(frozen=True)
class FeedRendering:
    """Response callbacks shared by source entries, bound at composition time."""

    send_item: Callable[[FeedItem], Awaitable[Any]]
    send_photo: SendPhoto
    answer: Callable[..., Awaitable[Any]]
    answer_photo: Callable[..., Awaitable[Any]]
    answer_video: Callable[..., Awaitable[Any]]
