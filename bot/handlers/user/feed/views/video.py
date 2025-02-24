from aiogram.types import BufferedInputFile

from services.gkfeed import FeedItem
from services.http import HttpService
from ui.keyboards.feed import FeedMarkup
from . import BaseFeedItemView


class VideoFeedItemView(BaseFeedItemView):
    async def _process_video_item(self, item: FeedItem):
        await self._send_video(item, item.link)

    async def _send_video(self, item: FeedItem, video_url: str):
        video_data = await HttpService.get(video_url)
        await self.bot.send_video(
            self.event.from_user.id,
            BufferedInputFile(video_data, "video.mp4"),
            caption=f'<a href="{item.link}">Link</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )
