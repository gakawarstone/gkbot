# Middleware user data retention

`UserDataMiddleware` supplies the existing mutable `data["data"]` dictionary to
handlers. One `UserDataStore` belongs to each dispatcher and is shared by message
and callback middleware. Separate dispatchers have separate stores. The current
middleware key remains the Telegram user ID. This change does not introduce chat
or topic isolation or change handler context classes.

## Stored values

- Form drafts include book names, authors, chapter counts, IDs and edited
  properties; reminder text, date and time; download filenames; and road setting
  names and values. These must survive between steps of their FSM flow.
- ChatGPT `messages` holds conversation history until that chat flow ends or
  becomes idle for the timeout.
- `message` holds a Telegram message that a form edits on later steps.
- `callback` holds the handler used to restart a pomodoro flow. It is needed
  while waiting for the yes/no response.
- `tz` is a timezone offset. TimeZoneMiddleware loads it again when needed.
- `delete_queue` holds Telegram messages to delete before the next message
  handler. It can outlive the form that produced it.

FSM storage's own `state.get_data()` values, such as task rows and feed module
drafts, are separate from this dictionary. They are not subject to this store's
entry limit. Database records and scheduled jobs are also outside this store.

## Lifetime and capacity

`USER_DATA_MAX_ENTRIES` defaults to 4096 and must be a positive integer.
`USER_DATA_IDLE_TTL_SECONDS` defaults to 3600 and must be a finite positive
number. Invalid values fail startup. The same values can be passed as
`max_entries` and `idle_ttl` to `UserDataStore` when embedding the bot.

Each entry counts toward the limit, including a dictionary currently in use by
a handler. No admission exceeds the limit. At capacity the store first removes
expired entries, then evicts the oldest idle entry without an active FSM, such as
a pending delete queue. If every slot belongs to a running handler or an
unexpired FSM, the middleware answers "Бот занят. Попробуйте ещё раз позже."
and skips the new handler. Existing sessions can continue using their entries.
This is an entry-count bound, not a byte limit on individual values or histories.

Acquiring an entry pins its dictionary until the handler and final FSM lookup
return. Expiry, capacity eviction, explicit cleanup and shutdown cannot remove
or clear a pinned dictionary. Concurrent handlers for the same key share the
same dictionary; cleanup waits for the last one. The store does not serialize
handlers or change aiogram's event isolation.

After the last handler returns, the idle timeout starts again. A waiting FSM
retains its dictionary until the next update, explicit cleanup, or idle timeout.
Expiry timers release abandoned entries even when no further updates arrive.
The timeout never interrupts an executing handler, even if it runs longer than
the timeout.

The middleware checks the final FSM state, after the handler's `finally` blocks.
`None` and states whose last component is `finish` complete the session, following
the bot's existing state naming convention. ChatGPT temporarily uses `FSM:finish`
while generating a response. If it returns to `FSM:get_message` before the
handler ends, its history stays intact.

On completion or `/exit`, the store drops the entry immediately when no deletion
queue remains. Otherwise it keeps only `delete_queue` until the next message
drains it, the idle timeout passes, or capacity pressure evicts it. Discarding an
entry never calls the Telegram API or deletes messages. Expired or evicted
pending messages may remain visible in Telegram. The remaining dictionary is
replaced rather than clearing objects that a handler may still reference.

If expiry, explicit cleanup, or a process restart leaves a nonterminal FSM with
no middleware entry, the next update clears that FSM and its FSM data, answers
"Сессия истекла. Запустите команду ещё раз." and skips the already-selected
handler. The user can then restart the command. This prevents a stale
`FSM:get_message` handler from receiving a dictionary without `messages`.
FSM state is reset on that next update; expiry itself only releases middleware
objects. Neither dictionaries nor timers persist across restarts.

## Explicit cleanup and extension contract

`UserDataMiddleware.store` exposes the dispatcher-owned store. Call
`store.cleanup(key)` to discard one dictionary; it returns whether an entry
existed. A pinned entry is marked for cleanup and removed when its last handler
returns. Until then, further acquisitions of that key reuse the same dictionary.
`store.clear()` requests cleanup for every entry and cancels expiry timers.
`UserDataMiddleware.close()` calls it on dispatcher shutdown. `store.expire()`
also permits a synchronous sweep of idle entries.

Use the store from the dispatcher's event loop. Keys are opaque `Hashable`
objects; future chat/topic scoping can pass a composite key to the same
`acquire`, `release` and `cleanup` methods. Each such key must consume a slot in
the same bounded store. Do not add an unbounded map beside it. Every successful
`acquire(key)` returns an entry and a `created` flag, and must have a matching
`release(key, entry, session_active=...)` in a `finally` block. Pass the final
session status after all handler work finishes. `entry.values` is the dictionary
to inject into `data["data"]`; a missing entry with a nonterminal FSM requires
the reset described above before invoking its selected handler.

The [aiogram 3.26 FSM documentation](https://docs.aiogram.dev/en/v3.26.0/dispatcher/finite_state_machine/index.html)
describes `FSMContext` state access and `clear()`. The implementation uses those
public methods and the
[middleware handler contract](https://docs.aiogram.dev/en/v3.26.0/dispatcher/middlewares.html).
