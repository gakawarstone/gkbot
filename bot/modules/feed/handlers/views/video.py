from aiogram.types import BufferedInputFile

from services.gkfeed import FeedItem
from services.http import HttpService
from ...ui.keyboards import FeedMarkup
from . import BaseFeedItemView


class VideoFeedItemView(BaseFeedItemView):
    async def _process_video_item(self, item: FeedItem):
        await self._send_video(item, item.link)

    async def _send_video(
        self, item: FeedItem, video_url: str, link_caption: str = "Link to video"
    ):
        video_url = await HttpService.get_redirected_url(video_url)
        video_data = await HttpService.get(video_url)
        await self.answer_video(
            BufferedInputFile(video_data, "video.mp4"),
            caption=f'<a href="{item.link}">{link_caption}</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )
