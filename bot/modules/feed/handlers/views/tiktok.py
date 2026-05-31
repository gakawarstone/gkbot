from aiogram.types import InputFile

from services.gkfeed import FeedItem
from services.tiktok import TikTokService
from . import BaseFeedItemView
from .video import VideoFeedItemView
from ...ui.keyboards import FeedMarkup


class TikTokFeedItemView(VideoFeedItemView, BaseFeedItemView):
    async def _process_tiktok_item(self, item: FeedItem):
        video = await TikTokService.get_video(item.link)

        await self._send_video_item(
            video.input_file,
            item,
            video.height,
            video.width,
            video.duration,
        )

    async def _send_video_item(
        self,
        video: str | InputFile,
        item: FeedItem,
        height: int | None = None,
        width: int | None = None,
        duration: int | None = None,
    ):
        await self.answer_video(
            video,
            caption=f'<a href="{item.link}">{item.link.split("@")[1].split("/")[0]}</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            height=height,
            width=width,
            duration=duration,
            supports_streaming=True,
        )
