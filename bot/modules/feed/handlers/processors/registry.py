from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Any

from services.gkfeed import FeedItem


@dataclass(frozen=True)
class FeedProcessor:
    """A source identity, its matching rule, and its bound item handler."""

    source_id: str
    matches: Callable[[FeedItem], bool]
    process: Callable[[FeedItem], Awaitable[Any]]


class FeedProcessorRegistry:
    """Resolve the first matching source without executing its handler."""

    def __init__(self, entries: Iterable[FeedProcessor]) -> None:
        self._entries = tuple(entries)
        source_ids = [entry.source_id for entry in self._entries]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Feed processor source identities must be unique")

    @property
    def entries(self) -> tuple[FeedProcessor, ...]:
        return self._entries

    def resolve(self, item: FeedItem) -> FeedProcessor | None:
        for entry in self._entries:
            if entry.matches(item):
                return entry
        return None
