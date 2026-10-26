from dataclasses import dataclass

from services.gkfeed import FeedItem

from .processors import FeedProcessorRegistry


@dataclass(frozen=True)
class FeedSourcePolicy:
    registry: FeedProcessorRegistry
    rejected_source_ids: frozenset[str] = frozenset()

    def allows(self, item: FeedItem) -> bool:
        entry = self.registry.resolve(item)
        return entry is None or entry.source_id not in self.rejected_source_ids
