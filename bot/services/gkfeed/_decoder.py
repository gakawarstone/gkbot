import json

from utils.process_worker import ProcessWorker

from ._types import FeedItemSummary


def _decode_items(payload: bytes) -> list[FeedItemSummary]:
    data = json.loads(payload)
    return [
        FeedItemSummary(
            id=raw_item["id"],
            feed_id=raw_item["feed_id"],
            link=raw_item["link"],
            title=raw_item["title"],
            date=raw_item["date"],
        )
        for raw_item in data["items"]
        if raw_item["link"]
    ]


class FeedDecoder(ProcessWorker):
    async def start(self) -> None:
        await self.decode(b'{"items":[]}')

    async def decode(self, payload: bytes) -> list[FeedItemSummary]:
        return await self.run(_decode_items, payload)
