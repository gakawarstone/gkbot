import logging
from collections.abc import Awaitable, Callable
from typing import Any

from services.gkfeed import FeedItem

from ._base import BaseHandler
from ._exceptions import RECOVERABLE_FEED_ERRORS
from .processors import FeedProcessorRegistry
from .processors.discours import create_discours_processor
from .processors.hltv import create_hltv_processor
from .processors.kinogo import create_kinogo_processor
from .processors.rezka import create_rezka_processor
from .processors.shiki import create_shiki_processor
from .processors.spoti import create_spoti_processor
from .processors.telegram import create_telegram_processor
from .processors.twitch import create_twitch_processor
from .views.base import BaseWebFeedItemView
from .views.instagram import InstagramFeedItemView
from .views.matreshka import MatreshkaFeedItemView
from .views.pornhub import PornhubFeedItemView
from .views.porno365 import Porno365FeedItemView
from .views.reddit import RedditFeedItemView
from .views.sasflix import SasflixFeedItemView
from .views.stories import StoriesFeedItemView
from .views.tiktok import TikTokFeedItemView
from .views.video import VideoFeedItemView
from .views.vk import VKFeedItemView
from .views.youtube import YoutubeFeedItemView

_ITEM_PROCESSOR = Callable[[FeedItem], Awaitable[Any]]
logger = logging.getLogger(__name__)


class _RedactedFeedError(Exception):
    """Keep error type and stack frames without URL/payload-bearing messages."""


class GkfeedItemProcessorExtension(
    SasflixFeedItemView,
    MatreshkaFeedItemView,
    InstagramFeedItemView,
    Porno365FeedItemView,
    PornhubFeedItemView,
    TikTokFeedItemView,
    StoriesFeedItemView,
    RedditFeedItemView,
    YoutubeFeedItemView,
    BaseWebFeedItemView,
    VideoFeedItemView,
    VKFeedItemView,
    BaseHandler,
):
    @property
    def _processor_registry(self) -> FeedProcessorRegistry:
        return FeedProcessorRegistry(
            (
                create_discours_processor(self._send_photo),
                create_kinogo_processor(self._send_photo, self._send_item),
                create_spoti_processor(self._send_photo, self._send_item),
                create_telegram_processor(self._send_photo, self._send_item),
                create_rezka_processor(self._send_photo, self._send_item),
                create_shiki_processor(self._send_photo),
                create_twitch_processor(self._send_photo),
                create_hltv_processor(self.answer_photo, self._send_item),
            )
        )

    @property
    def _processors(self) -> dict[str, _ITEM_PROCESSOR]:
        # TODO: create filters for processor matching instead of startswith prefixes.
        return {
            "https://stor": self._process_stories_item,
            "https://vk": self._process_vk_item,
            "https://www.youtube": self._process_youtube_item,
            "https://www.reddit.com": self._process_reddit_item,
            "https://www.tiktok": self._process_tiktok_item,
            "https://www.pornhub.com": self._process_pornhub_item,
            "https://de.pornhub.org": self._process_pornhub_item,
            "https://pornhub.org": self._process_pornhub_item,
            "http://porno365.broker": self._process_porno365_item,
            "https://instagram.com": self._process_instagram_item,
            "https://www.instagram.com": self._process_instagram_item,
            "https://sasflix.ru/": self._process_sasflix_item,
            "https://matreshka.tv/video/": self._process_matreshka_item,
        }

    async def _process_item(self, item: FeedItem) -> None:
        entry = self._processor_registry.resolve(item)
        if entry is not None:
            await self._run_processor(item, entry.process, entry.source_id)
            return

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
