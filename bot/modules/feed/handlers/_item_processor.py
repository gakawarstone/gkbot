import logging
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from services.gkfeed import FeedItem

from ._exceptions import RECOVERABLE_FEED_ERRORS
from .policy import FeedSourcePolicy
from .processors import FeedProcessorRegistry
from .processors.discours import create_discours_processor
from .processors.hltv import create_hltv_processor
from .processors.instagram import create_instagram_processor
from .processors.kinogo import create_kinogo_processor
from .processors.matreshka import create_matreshka_processor
from .processors.pornhub import create_pornhub_processor
from .processors.porno365 import create_porno365_processor
from .processors.reddit import create_reddit_processor
from .processors.rendering import FeedRendering
from .processors.rezka import create_rezka_processor
from .processors.sasflix import create_sasflix_processor
from .processors.shiki import create_shiki_processor
from .processors.spoti import create_spoti_processor
from .processors.stories import create_stories_processor
from .processors.telegram import create_telegram_processor
from .processors.tiktok import create_tiktok_processor
from .processors.twitch import create_twitch_processor
from .processors.vk import create_vk_processor
from .processors.youtube import create_youtube_processor
from .views.base import BaseWebFeedItemView

_ITEM_PROCESSOR = Callable[[FeedItem], Awaitable[Any]]
logger = logging.getLogger(__name__)


class _RedactedFeedError(Exception):
    """Keep error type and stack frames without URL/payload-bearing messages."""


class GkfeedItemProcessorExtension(BaseWebFeedItemView):
    _rejected_source_ids: ClassVar[frozenset[str]] = frozenset()

    @property
    def _source_policy(self) -> FeedSourcePolicy:
        return FeedSourcePolicy(self._processor_registry, self._rejected_source_ids)

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
                create_kinogo_processor(self._send_photo, self._send_item),
                create_spoti_processor(self._send_photo, self._send_item),
                create_vk_processor(rendering),
                create_youtube_processor(rendering),
                create_telegram_processor(self._send_photo, self._send_item),
                create_reddit_processor(rendering),
                create_rezka_processor(self._send_photo, self._send_item),
                create_shiki_processor(self._send_photo),
                create_twitch_processor(self._send_photo),
                create_tiktok_processor(rendering),
                create_pornhub_processor(rendering),
                create_porno365_processor(rendering),
                create_discours_processor(self._send_photo),
                create_instagram_processor(rendering),
                create_hltv_processor(self.answer_photo, self._send_item),
                create_sasflix_processor(rendering),
                create_matreshka_processor(rendering),
            )
        )

    async def _process_item(self, item: FeedItem) -> None:
        entry = self._processor_registry.resolve(item)
        if entry is not None:
            await self._run_processor(item, entry.process, entry.source_id)
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
