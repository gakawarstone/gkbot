# Middleware user data retention

`UserDataMiddleware` injects a mutable `UserData` dictionary as `data["data"]`.
One dispatcher-owned `UserDataStore` serves messages and callbacks, currently
keyed by Telegram user ID across chats. Each new dictionary contains
`delete_queue: []`. Separate dispatchers have separate stores.

The [middleware inventory](middleware-data.md#user-cache-inventory) lists the
stored fields. Form drafts, editable message references, pomodoro restart
callbacks and ChatGPT history must survive between FSM steps. Timezone middleware
reloads `tz` when needed; pending deletions can outlive the flow that queued them.
FSM storage's `state.get_data()`, database records and scheduled jobs are separate
and are not bounded by this store. Middleware dictionaries do not survive restart.

## Lifetime and limits

`USER_DATA_MAX_ENTRIES` defaults to 4096 and must be a positive integer.
`USER_DATA_IDLE_TTL_SECONDS` defaults to 3600 and must be finite and positive.
Invalid settings fail startup. Embedded users can supply `max_entries` and
`idle_ttl` to `UserDataStore` instead. The limit counts entries, not bytes within
a dictionary or conversation history.

A handler pins its dictionary through its final FSM lookup. Expiry, eviction,
explicit cleanup and shutdown cannot remove a pinned entry. Concurrent handlers
for the same key share data; cleanup waits for the last one. The store does not
serialize handlers or change aiogram event isolation.

The idle timeout starts after the last handler returns and refreshes with further
activity. Timers release abandoned entries even without new updates. Unexpired
waiting FSM sessions remain available, and an executing handler can exceed the
idle timeout safely.

Completion follows the bot's final state convention: `None` or a state whose last
component is `finish`. The middleware checks after the handler returns, so ChatGPT's temporary
`FSM:finish` during generation does not discard history if it returns to
`FSM:get_message`. Completion or `/exit` drops context, keeping only a nonempty
`delete_queue` for the next message to drain.

At capacity, expired entries go first, then the oldest idle entry without an
active FSM. If all slots belong to running handlers or unexpired sessions, new
keys receive a busy response and their handlers are skipped. Discarding a queue
on expiry or eviction makes no Telegram API calls; its messages may remain
visible in Telegram.

If an entry is missing but its FSM is nonterminal, the next update clears that
FSM and its FSM data, asks the user to restart, and skips the selected handler.
This prevents handlers from receiving partial context after expiry, explicit
cleanup or restart. Expiry itself only releases middleware objects.

## Store contract

Access the store through `UserDataMiddleware.store` on the dispatcher's event loop.
`acquire(key)` returns an entry
and a `created` flag; inject `entry.values` and pair every acquisition with
`release(key, entry, session_active=...)` in `finally`, using the final FSM status.
A new entry with a nonterminal FSM needs the reset described above.

`cleanup(key)` reports whether an entry existed and defers removal while pinned.
`clear()` applies cleanup to all entries and cancels timers; middleware `close()`
runs it at dispatcher shutdown. `expire()` also permits an explicit idle sweep.
Keys accept `Hashable` objects. Any future chat/topic keys must consume slots in
this same bounded store rather than a separate unbounded mapping.
