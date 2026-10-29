import json

from utils.process_worker import ProcessWorker

from ._types import FeedItem


def feed_item_from_raw_data(raw_data: dict) -> FeedItem:
    return FeedItem(
        id=raw_data["id"],
        feed_id=raw_data["feed_id"],
        link=raw_data["link"],
        title=raw_data["title"],
        text=raw_data["text"],
    )


def _decode_items(payload: bytes) -> list[FeedItem]:
    data = json.loads(payload)
    return [
        feed_item_from_raw_data(raw_item)
        for raw_item in data["items"]
        if raw_item["link"]
    ]


class FeedDecoder(ProcessWorker):
    async def start(self) -> None:
        await self.decode(b'{"items":[]}')

    async def decode(self, payload: bytes) -> list[FeedItem]:
        return await self.run(_decode_items, payload)
