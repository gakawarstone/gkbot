from services.gkfeed import FeedItem
from services.matreshka import MatreshkaService

from ...ui.keyboards.matreshka import MatreshkaFeedItemMarkup
from .matching import matches_source_url
from .registry import FeedProcessor
from .rendering import FeedRendering


def create_matreshka_processor(rendering: FeedRendering) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        video = await MatreshkaService.get_video(item.link)
        if video.image_url is None:
            return await rendering.send_item(item)

        await rendering.send_photo(
            item=item,
            media_url=video.image_url,
            description=video.title,
            link_caption="МатрёшкаТВ",
            reply_markup=MatreshkaFeedItemMarkup.get_item_markup(
                item.id,
                video.id,
            ),
        )

    return FeedProcessor(
        "matreshka",
        lambda item: matches_source_url(
            item, frozenset({"matreshka.tv"}), path_prefix="/video/"
        ),
        process,
    )
