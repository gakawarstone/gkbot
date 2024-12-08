from services.gkfeed import FeedItem
from ._base import BaseHandler
from .piokok._extentions import PiokokFeedItemRepresentationExtention


class GkfeedItemProcessorExtention(PiokokFeedItemRepresentationExtention, BaseHandler):
    async def _process_item(self, item: FeedItem):
        if item.link.startswith("https://www.piokok"):
            await self._process_piokok_item(item)
            return

        await self._send_item(item)
