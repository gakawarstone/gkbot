from typing import Awaitable, Callable

from services.gkfeed import FeedItem
from ._base import BaseHandler
from .views.video import VideoFeedItemView
from .views.kinogo import KinogoFeedItemView
from .views.spoti import SpotiFeedItemView
from .views.base import BaseWebFeedItemView
from .views.vk import VKFeedItemView
from .views.piokok import PiokokFeedItemView

_ITEM_PROCESSOR = Callable[[FeedItem], Awaitable[None]]


class GkfeedItemProcessorExtention(
    PiokokFeedItemView,
    BaseWebFeedItemView,
    KinogoFeedItemView,
    VideoFeedItemView,
    SpotiFeedItemView,
    VKFeedItemView,
    BaseHandler,
):
    @property
    def _processors(self) -> dict[str, _ITEM_PROCESSOR]:
        return {
            "https://www.piokok": self._process_piokok_item,
            "https://stor": self._process_video_item,
            "https://kinogo": self._process_kinogo_item,
            "https://open": self._process_spoti_item,
            "https://vk": self._process_vk_item,
            "https://www.youtube": self._process_base_item,
            "https://www.tagesschau": self._process_base_item,
            "https://trashbox": self._process_base_item,
            "https://shikimori": self._process_base_item,
            "https://hdrezka.me": self._process_base_item,
        }

    async def _process_item(self, item: FeedItem):
        for proc_key in self._processors.keys():
            if item.link.startswith(proc_key):
                await self._processors[proc_key](item)
                return
        await self._send_item(item)
