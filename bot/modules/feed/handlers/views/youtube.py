from aiogram.types import URLInputFile

from services.gkfeed import FeedItem
from services.youtube import YoutubeApiService, UnavailableVideo
from ...ui.keyboards.youtube import YoutubeFeedItemMarkup
from . import BaseFeedItemView


class YoutubeFeedItemView(BaseFeedItemView):
    async def _process_youtube_item(self, item: FeedItem):
        try:
            data = await YoutubeApiService.get_video_data(item.link)
            video_code = item.link.split("=")[-1]
            await self.answer_photo(
                URLInputFile(data.thumbnail_url),
                caption=f'<b>{data.title}</b>\n\n<a href="{item.link}">{data.channel_title}</a>',
                reply_markup=YoutubeFeedItemMarkup.get_item_markup(item.id, video_code),
            )
        except UnavailableVideo:
            await self._send_item(item)
