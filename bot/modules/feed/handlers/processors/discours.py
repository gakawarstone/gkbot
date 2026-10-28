from collections.abc import Awaitable, Callable

from services.gkfeed import FeedItem
from services.http import HttpService

from .matching import matches_source_url
from .registry import FeedProcessor


def create_discours_processor(
    send_photo: Callable[[FeedItem, str, str], Awaitable[None]],
) -> FeedProcessor:
    async def process(item: FeedItem) -> None:
        item_id = item.link.split("/")[-1]
        api_endpoint = f"https://api.discours.io/api/v2/content-items/{item_id}"
        data = await HttpService.get_json(api_endpoint)
        title = data["data"]["title"]
        media_url = (
            "https://assets.discours.io/unsafe/900x/" + data["data"]["thumborId"]
        )
        await send_photo(item, str(media_url), str(title))

    return FeedProcessor(
        "discours",
        lambda item: matches_source_url(item, frozenset({"discours.io"})),
        process,
    )
