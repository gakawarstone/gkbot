import logging
from collections.abc import Awaitable, Callable
from typing import Any

from services.gkfeed import FeedItem

from ._base import BaseHandler
from ._exceptions import RECOVERABLE_FEED_ERRORS
from .processors import FeedProcessorRegistry
from .processors.discours import create_discours_processor
from .processors.instagram import create_instagram_processor
from .processors.matreshka import create_matreshka_processor
from .processors.pornhub import create_pornhub_processor
from .processors.porno365 import create_porno365_processor
from .processors.reddit import create_reddit_processor
from .processors.rendering import FeedRendering
from .processors.sasflix import create_sasflix_processor
from .processors.stories import create_stories_processor
from .processors.tiktok import create_tiktok_processor
from .processors.vk import create_vk_processor
from .processors.youtube import create_youtube_processor
from .views.base import BaseWebFeedItemView
from .views.hltv import HltvFeedItemView
from .views.kinogo import KinogoFeedItemView
from .views.rezka import RezkaFeedItemView
from .views.shiki import ShikiFeedItemView
from .views.spoti import SpotiFeedItemView
from .views.tg import TelegramFeedItemView
from .views.twitch import TwitchFeedItemView

_ITEM_PROCESSOR = Callable[[FeedItem], Awaitable[Any]]
logger = logging.getLogger(__name__)


class _RedactedFeedError(Exception):
    """Keep error type and stack frames without URL/payload-bearing messages."""


class GkfeedItemProcessorExtension(
    HltvFeedItemView,
    TwitchFeedItemView,
    ShikiFeedItemView,
    RezkaFeedItemView,
    TelegramFeedItemView,
    BaseWebFeedItemView,
    KinogoFeedItemView,
    SpotiFeedItemView,
    BaseHandler,
):
    @property
    def _processor_registry(self) -> FeedProcessorRegistry:
        rendering = FeedRendering(
            send_item=self._send_item,
            send_photo=self._send_photo,
            answer=self.answer,
            answer_photo=self.answer_photo,
            answer_video=self.answer_video,
        )
        return FeedProcessorRegistry(
            (
                create_stories_processor(rendering, lambda: self._gkfeed_credentials),
                create_vk_processor(rendering),
                create_youtube_processor(rendering),
                create_reddit_processor(rendering),
                create_tiktok_processor(rendering),
                create_pornhub_processor(rendering),
                create_porno365_processor(rendering),
                create_discours_processor(self._send_photo),
                create_instagram_processor(rendering),
                create_sasflix_processor(rendering),
                create_matreshka_processor(rendering),
            )
        )

    @property
    def _processors(self) -> dict[str, _ITEM_PROCESSOR]:
        # TODO: create filters for processor matching instead of startswith prefixes.
        return {
            "https://kinogo": self._process_kinogo_item,
            "https://open": self._process_spoti_item,
            "https://t.me": self._process_telegram_item,
            "https://hdrezka.me": self._process_rezka_item,
            "https://shikimori": self._process_shiki_item,
            "https://www.twitch": self._process_twitch_item,
            "https://www.hltv.org": self._process_hltv_item,
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
