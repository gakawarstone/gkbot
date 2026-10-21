from services.gkfeed import FeedItem
from services.open_graph import OpenGraphService
from services.sasflix import SasflixService

from ...ui.keyboards.sasflix import SasflixFeedItemMarkup
from . import BaseFeedItemView


class SasflixFeedItemView(BaseFeedItemView):
    async def _process_sasflix_item(self, item: FeedItem) -> None:
        await SasflixService.get_audio(item.link)
        metadata = await OpenGraphService.get(item.link)
        if metadata.image_url is None:
            return await self._send_item(item)

        await self._send_photo(
            item=item,
            media_url=metadata.image_url,
            description=metadata.title or item.title,
            link_caption="Sasflix",
            reply_markup=SasflixFeedItemMarkup.get_item_markup(
                item.id,
                SasflixService.get_topic_uuid(item.link),
            ),
        )
