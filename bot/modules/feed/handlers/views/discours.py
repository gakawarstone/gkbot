from services.http import HttpService
from services.gkfeed import FeedItem
from . import BaseFeedItemView


class DiscoursFeedItemView(BaseFeedItemView):
    async def _process_discours_item(self, item: FeedItem):
        item_id = item.link.split("/")[-1]
        api_endpoint = f"https://api.discours.io/api/v2/content-items/{item_id}"

        data = await HttpService.get_json(api_endpoint)
        title = data["data"]["title"]
        media_url = (
            "https://assets.discours.io/unsafe/900x/" + data["data"]["thumborId"]
        )

        await self._send_photo(item, str(media_url), str(title))
