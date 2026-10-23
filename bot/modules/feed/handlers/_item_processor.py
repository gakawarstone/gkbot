import logging
from collections.abc import Awaitable, Callable
from typing import Any

from services.gkfeed import FeedItem

from ._base import BaseHandler
from ._exceptions import RECOVERABLE_FEED_ERRORS
from .views.base import BaseWebFeedItemView
from .views.discours import DiscoursFeedItemView
from .views.hltv import HltvFeedItemView
from .views.instagram import InstagramFeedItemView
from .views.kinogo import KinogoFeedItemView
from .views.matreshka import MatreshkaFeedItemView
from .views.pornhub import PornhubFeedItemView
from .views.porno365 import Porno365FeedItemView
from .views.reddit import RedditFeedItemView
from .views.rezka import RezkaFeedItemView
from .views.sasflix import SasflixFeedItemView
from .views.shiki import ShikiFeedItemView
from .views.spoti import SpotiFeedItemView
from .views.stories import StoriesFeedItemView
from .views.tg import TelegramFeedItemView
from .views.tiktok import TikTokFeedItemView
from .views.twitch import TwitchFeedItemView
from .views.video import VideoFeedItemView
from .views.vk import VKFeedItemView
from .views.youtube import YoutubeFeedItemView

_ITEM_PROCESSOR = Callable[[FeedItem], Awaitable[Any]]
logger = logging.getLogger(__name__)


class _RedactedFeedError(Exception):
    """Keep error type and stack frames without URL/payload-bearing messages."""


class GkfeedItemProcessorExtension(
    SasflixFeedItemView,
    HltvFeedItemView,
    MatreshkaFeedItemView,
    InstagramFeedItemView,
    DiscoursFeedItemView,
    Porno365FeedItemView,
    PornhubFeedItemView,
    TikTokFeedItemView,
    TwitchFeedItemView,
    StoriesFeedItemView,
    ShikiFeedItemView,
    RezkaFeedItemView,
    RedditFeedItemView,
    TelegramFeedItemView,
    YoutubeFeedItemView,
    BaseWebFeedItemView,
    KinogoFeedItemView,
    VideoFeedItemView,
    SpotiFeedItemView,
    VKFeedItemView,
    BaseHandler,
):
    @property
    def _processors(self) -> dict[str, _ITEM_PROCESSOR]:
        # TODO: create filters for processor matching instead of startswith prefixes.
        return {
            "https://stor": self._process_stories_item,
            "https://kinogo": self._process_kinogo_item,
            "https://open": self._process_spoti_item,
            "https://vk": self._process_vk_item,
            "https://www.youtube": self._process_youtube_item,
            "https://t.me": self._process_telegram_item,
            "https://www.reddit.com": self._process_reddit_item,
            "https://hdrezka.me": self._process_rezka_item,
            "https://shikimori": self._process_shiki_item,
            "https://www.twitch": self._process_twitch_item,
            "https://www.tiktok": self._process_tiktok_item,
            "https://www.pornhub.com": self._process_pornhub_item,
            "https://de.pornhub.org": self._process_pornhub_item,
            "https://pornhub.org": self._process_pornhub_item,
            "http://porno365.broker": self._process_porno365_item,
            "https://discours.io": self._process_discours_item,
            "https://instagram.com": self._process_instagram_item,
            "https://www.instagram.com": self._process_instagram_item,
            "https://www.hltv.org": self._process_hltv_item,
            "https://sasflix.ru/": self._process_sasflix_item,
            "https://matreshka.tv/video/": self._process_matreshka_item,
        }

    async def _process_item(self, item: FeedItem) -> None:
        for prefix, processor in self._processors.items():
            if item.link.startswith(prefix):
                processor_name = getattr(
                    processor, "__name__", type(processor).__name__
                )
                await self._run_processor(item, processor, processor_name)
                return

        await self._run_processor(item, self._process_base_item, "_process_base_item")

    async def _run_processor(
        self, item: FeedItem, processor: _ITEM_PROCESSOR, processor_name: str
    ) -> None:
        try:
            await processor(item)
        except RECOVERABLE_FEED_ERRORS as error:
            # Exception messages and chains can contain credentials, URLs or media.
            # Preserve the original frames, but log only the exception class name.
            safe_error = _RedactedFeedError(type(error).__name__)
            logger.error(
                "Failed to process feed item id=%s feed_id=%s text_length=%s processor=%s",
                item.id,
                item.feed_id,
                len(item.text),
                processor_name[:80],
                exc_info=(type(safe_error), safe_error, error.__traceback__),
            )
            await self._send_item(item)
