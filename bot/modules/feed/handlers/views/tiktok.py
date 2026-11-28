from services.gkfeed import FeedItem
from services.tiktok import TikTokService
from ui.media import media_input_file

from ...ui.keyboards import FeedMarkup
from . import BaseFeedItemView
from .video import VideoFeedItemView


class TikTokFeedItemView(VideoFeedItemView, BaseFeedItemView):
    async def _process_tiktok_item(self, item: FeedItem) -> None:
        video = await TikTokService.get_video(item.link)

        await self.answer_video(
            media_input_file(video.file, protect_from_cleanup=True),
            caption=f'<a href="{item.link}">{item.link.split("@")[1].split("/")[0]}</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            height=video.height,
            width=video.width,
            duration=video.duration,
            supports_streaming=True,
        )
