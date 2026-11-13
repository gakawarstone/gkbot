from aiogram.types import URLInputFile

from services.gkfeed import FeedItem
from services.youtube import UnavailableVideo, YoutubeApiService
from utils.strings import remove_emoji

from ...ui.keyboards.youtube import YoutubeFeedItemMarkup
from .matching import matches_source_url
from .registry import FeedProcessor
from .rendering import FeedRendering


def create_youtube_processor(rendering: FeedRendering) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        try:
            data = await YoutubeApiService.get_video_data(item.link)
            video_code = item.link.split("=")[-1]
            channel_title = remove_emoji(data.channel_title)
            await rendering.answer_photo(
                URLInputFile(data.thumbnail_url),
                caption=f'<b>{data.title}</b>\n\n<a href="{item.link}">{channel_title}</a>',
                reply_markup=YoutubeFeedItemMarkup.get_item_markup(item.id, video_code),
            )
        except UnavailableVideo:
            await rendering.send_item(item)

    return FeedProcessor(
        "youtube",
        lambda item: matches_source_url(item, frozenset({"www.youtube.com"})),
        process,
    )
