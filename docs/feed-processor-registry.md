# Feed processor registry

`modules.feed.handlers.processors` exports `FeedProcessor` and
`FeedProcessorRegistry`. An entry owns a stable `source_id`, a synchronous
`matches(FeedItem) -> bool` predicate, and an async `process(FeedItem)` callback.
Source identities name sources, never URLs, payloads or user values.

`FeedProcessorRegistry(entries)` stores an ordered tuple exposed by the read-only
`entries` property. Duplicate source identities raise `ValueError`.
`resolve(item)` returns the first match or `None`, without executing handlers or
catching matching errors. Construction and matching must not perform network I/O.

Each source factory returns a bound entry and accepts rendering dependencies
explicitly. `processors.discours.create_discours_processor(send_photo)` takes
`Callable[[FeedItem, str, str], Awaitable[None]]`; the shared photo sender retains
caption, keyboard and Telegram fallback behavior.

The handler composes entries in `_processor_registry`. Resolve outside the
exception boundary, then call
`await self._run_processor(item, entry.process, entry.source_id)`.
The [feed exception contract](feed-processor-exceptions.md) applies unchanged.

Only Discours is registered in this layer. Registry misses use legacy dispatch,
then the generic web view. Each later migration removes its own legacy entries
and inheritance while preserving keyboard builders and callback payloads.
Discours retains the original `https://discours.io` prefix semantics, including
longer hostnames starting with that text. Hostname validation and new aliases
remain separate routing changes for task 13.
