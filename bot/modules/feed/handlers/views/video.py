from aiogram.types import BufferedInputFile, InputFile

from services.gkfeed import FeedItem
from services.http import HttpService
from services.video import VideoMetadata
from ui.video import send_video

from ...ui.keyboards import FeedMarkup
from . import BaseFeedItemView


class VideoFeedItemView(BaseFeedItemView):
    async def _send_video(
        self, item: FeedItem, video_url: str, link_caption: str = "Link to video"
    ) -> None:
        video_url = await HttpService.get_redirected_url(video_url)
        video_data = await HttpService.get(video_url)
        await self.answer_video(
            BufferedInputFile(video_data, "video.mp4"),
            caption=f'<a href="{item.link}">{link_caption}</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    async def _send_video_item(
        self,
        video: str | InputFile,
        item: FeedItem,
        height: int | None = None,
        width: int | None = None,
        duration: int | None = None,
        *,
        caption: str | None = None,
        metadata: VideoMetadata | None = None,
    ) -> None:
        await send_video(
            self.answer_video,
            video,
            metadata=metadata,
            caption=caption
            if caption is not None
            else f'<a href="{item.link}">Link to video</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            height=height,
            width=width,
            duration=duration,
            supports_streaming=True,
        )
