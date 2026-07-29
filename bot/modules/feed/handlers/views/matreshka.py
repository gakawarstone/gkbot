from services.gkfeed import FeedItem
from services.matreshka import MatreshkaService

from ...ui.keyboards.matreshka import MatreshkaFeedItemMarkup
from . import BaseFeedItemView


class MatreshkaFeedItemView(BaseFeedItemView):
    async def _process_matreshka_item(self, item: FeedItem) -> None:
        video = await MatreshkaService.get_video(item.link)
        if video.image_url is None:
            return await self._send_item(item)

        await self._send_photo(
            item=item,
            media_url=video.image_url,
            description=video.title,
            link_caption="МатрёшкаТВ",
            reply_markup=MatreshkaFeedItemMarkup.get_item_markup(
                item.id,
                video.id,
            ),
        )
