from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputFile

from services.gkfeed import FeedItem
from services.tiktok import TikTokService, TikTokVideoUrlExtractionFailed
from . import BaseFeedItemView
from .video import VideoFeedItemView
from ...ui.keyboards import FeedMarkup


class TikTokFeedItemView(VideoFeedItemView, BaseFeedItemView):
    async def _process_tiktok_item(self, item: FeedItem):
        try:
            video = await TikTokService.get_video_url(item.link)
            await self._send_video_item(video, item)
        except (TelegramBadRequest, TikTokVideoUrlExtractionFailed):
            video = await TikTokService.get_video_as_input_file(item.link)
            await self._send_video_item(video, item)

    async def _send_video_item(self, video: str | InputFile, item: FeedItem):
        await self.answer_video(
            video,
            caption=f'<a href="{item.link}">{item.link.split("@")[1].split("/")[0]}</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )
