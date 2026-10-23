import asyncio
import math
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from time import monotonic
from typing import Any


class UserDataCapacityError(RuntimeError):
    """All slots belong to running handlers or unexpired FSM sessions."""


@dataclass
class UserDataEntry:
    values: dict[str, Any] = field(default_factory=dict)
    active_handlers: int = 0
    session_active: bool = False
    cleanup_pending: bool = False
    last_used: float = 0.0
    timer: asyncio.TimerHandle | None = None


class UserDataStore:
    """Bound in-memory dictionaries, pinning them while a handler holds them.

    Use one store per dispatcher and access it from that dispatcher's event loop.
    Keys remain opaque so session scoping can change independently of retention.
    """

    def __init__(
        self,
        *,
        max_entries: int = 4096,
        idle_ttl: float = 3600,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        if not math.isfinite(idle_ttl) or idle_ttl <= 0:
            raise ValueError("idle_ttl must be finite and positive")
        self.max_entries = max_entries
        self.idle_ttl = idle_ttl
        self._clock = clock
        self._entries: dict[Hashable, UserDataEntry] = {}

    def __len__(self) -> int:
        return len(self._entries)

    def acquire(self, key: Hashable) -> tuple[UserDataEntry, bool]:
        """Pin a dictionary, refusing admission rather than evicting a live flow."""
        self.expire()
        entry = self._entries.get(key)
        created = entry is None
        if entry is None:
            if len(self) >= self.max_entries:
                self._evict_idle()
            entry = UserDataEntry()
            self._entries[key] = entry
        if entry.timer is not None:
            entry.timer.cancel()
            entry.timer = None
        entry.active_handlers += 1
        return entry, created

    def release(
        self, key: Hashable, entry: UserDataEntry, *, session_active: bool
    ) -> None:
        """Release a pin after the handler and its final FSM lookup finish."""
        entry.session_active = session_active
        entry.active_handlers -= 1
        if entry.active_handlers:
            return
        if entry.cleanup_pending:
            self.cleanup(key)
            return
        if not session_active:
            queue = entry.values.get("delete_queue")
            if not queue:
                self.cleanup(key)
                return
            # Replace the mapping instead of clearing objects held by old handlers.
            entry.values = {"delete_queue": queue}
        entry.last_used = self._clock()
        entry.timer = asyncio.get_running_loop().call_later(
            self.idle_ttl, self.cleanup, key
        )

    def cleanup(self, key: Hashable) -> bool:
        """Drop one entry, deferring removal until its last handler returns."""
        entry = self._entries.get(key)
        if entry is None:
            return False
        if entry.timer is not None:
            entry.timer.cancel()
            entry.timer = None
        if entry.active_handlers:
            entry.cleanup_pending = True
        else:
            del self._entries[key]
        return True

    def clear(self) -> None:
        """Cancel expiry timers and release entries, respecting active handlers."""
        for key in list(self._entries):
            self.cleanup(key)

    def expire(self) -> None:
        """Sweep abandoned entries without touching executing handlers."""
        now = self._clock()
        for key, entry in list(self._entries.items()):
            if not entry.active_handlers and now - entry.last_used >= self.idle_ttl:
                self.cleanup(key)

    def _evict_idle(self) -> None:
        candidates = (
            (key, entry)
            for key, entry in self._entries.items()
            if not entry.active_handlers and not entry.session_active
        )
        oldest = min(candidates, key=lambda item: item[1].last_used, default=None)
        if oldest is None:
            raise UserDataCapacityError("User data store is full")
        self.cleanup(oldest[0])
