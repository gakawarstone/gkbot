from services.gkfeed import FeedItem
from services.tiktok import TikTokService

from . import BaseFeedItemView
from .video import VideoFeedItemView


class TikTokFeedItemView(VideoFeedItemView, BaseFeedItemView):
    async def _process_tiktok_item(self, item: FeedItem) -> None:
        video = await TikTokService.get_video(item.link)

        await self._send_video_item(
            video.input_file,
            item,
            video.height,
            video.width,
            video.duration,
            caption=f'<a href="{item.link}">{item.link.split("@")[1].split("/")[0]}</a>',
            metadata=video,
        )
