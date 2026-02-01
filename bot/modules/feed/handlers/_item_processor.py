from typing import Awaitable, Callable, Any

from services.gkfeed import FeedItem
from ._base import BaseHandler
from .views.video import VideoFeedItemView
from .views.kinogo import KinogoFeedItemView
from .views.spoti import SpotiFeedItemView
from .views.base import BaseWebFeedItemView
from .views.vk import VKFeedItemView
from .views.piokok import PiokokFeedItemView
from .views.youtube import YoutubeFeedItemView
from .views.tg import TelegramFeedItemView
from .views.reddit import RedditFeedItemView
from .views.rezka import RezkaFeedItemView
from .views.shiki import ShikiFeedItemView
from .views.stories import StoriesFeedItemView
from .views.twitch import TwitchFeedItemView
from .views.tiktok import TikTokFeedItemView
from .views.pornhub import PornhubFeedItemView
from .views.discours import DiscoursFeedItemView
# from .views.instagram import InstagramFeedItemView

_ITEM_PROCESSOR = Callable[[FeedItem], Awaitable[Any]]


class GkfeedItemProcessorExtension(
    # InstagramFeedItemView,
    DiscoursFeedItemView,
    PornhubFeedItemView,
    TikTokFeedItemView,
    TwitchFeedItemView,
    StoriesFeedItemView,
    ShikiFeedItemView,
    RezkaFeedItemView,
    RedditFeedItemView,
    TelegramFeedItemView,
    YoutubeFeedItemView,
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
            "https://discours.io": self._process_discours_item,
            # "https://instagram.com": self._process_instagram_item,
            # "https://www.instagram.com": self._process_instagram_item,
        }

    async def _process_item(self, item: FeedItem):
        try:
            for proc_key in self._processors.keys():
                if item.link.startswith(proc_key):
                    await self._processors[proc_key](item)
                    return

            await self._process_base_item(item)
        except Exception:
            await self._send_item(item)
            print("Failed to process item: ", item)

