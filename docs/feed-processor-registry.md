# Feed processor registry

`modules.feed.handlers.processors` exports `FeedProcessor` and
`FeedProcessorRegistry`. A frozen `FeedProcessor` contains:

```python
source_id: str
matches: Callable[[FeedItem], bool]
process: Callable[[FeedItem], Awaitable[Any]]
```

`source_id` is a stable source name, such as `discours`, shared by all items and
aliases for that source. It must not contain item URLs, payloads or user values.
`matches` is a synchronous source-owned predicate. `process` handles a selected
item; the discours implementation returns `None`.

`FeedProcessorRegistry(entries: Iterable[FeedProcessor])` copies entries into an
ordered tuple exposed by the read-only `entries` property. Duplicate identities
raise `ValueError`. `resolve(item)` returns the first matching entry or `None`.
It does not execute handlers or catch matching errors. Constructing entries and
matching them must not perform network requests.

## Source factories and composition

Each source module supplies a factory returning a bound `FeedProcessor`.
`processors.discours.create_discours_processor(send_photo)` accepts
`Callable[[FeedItem, str, str], Awaitable[None]]`. Its process callback owns the
Discours JSON request and extraction. It uses the existing shared photo sender
for the caption, keyboard and Telegram photo fallback.

`GkfeedItemProcessorExtension._processor_registry` composes the entries for each
handler. Factories receive dependencies explicitly, without depending on the
processor multiple-inheritance hierarchy. Other sources may accept different
rendering callbacks or a typed rendering dependency according to their needs.
Add their entries to the composition property in a deliberate order.

```python
entry = self._processor_registry.resolve(item)
if entry is not None:
    await self._run_processor(item, entry.process, entry.source_id)
    return
```

Resolution occurs outside the shared execution boundary. Selected processor
errors follow the [feed exception contract](feed-processor-exceptions.md).
Recoverable failures send the original plain link once and log bounded source
identity. Programming errors and cancellation propagate. Failure never tries a
second processor or generic web extraction, and fallback sender errors propagate.

## Migration behavior

`discours` and the ten [specialized sources](feed-specialized-processors.md) use
the registry. Their inherited views and legacy entries have been removed. They
retain their existing endpoints, captions, media and keyboard behavior. A
registry miss uses the remaining simple-source legacy dispatch; a legacy miss
uses the generic web view. All remaining prefix routes keep their order.

Discours matching retains the original `https://discours.io` prefix semantics,
including acceptance of longer hostnames starting with that text. This migration
introduces no hostname validation or new aliases. Task 13 owns completion of the
filters/startswith TODO; changes to accepted URLs need separate regression cases.

The agreed source ownership is:

- Task 10: registry and `discours`.
- Task 11: `kinogo`, `spoti`, `rezka`, `shiki`, `telegram`, `hltv`, `twitch`.
- Task 12: `stories`, `vk`, `youtube`, `reddit`, `tiktok`, `pornhub`, `porno365`,
  `instagram`, `sasflix`, `matreshka`. Video is a helper, not a source.
- Task 13: integrate migrations and remove processor multiple inheritance.

Keep each source's existing keyboard builder and callback payloads during
migration. Remove only that source's legacy prefix entries, imports and view
inheritance once its standalone factory is registered.

## Regression coverage

`bot/tests/handlers/test_feed_processor_registry.py` checks ordered resolution,
unknown sources, duplicate identities, matching-error propagation, precedence over
legacy dispatch, and Discours prefix compatibility. Offline rendering tests cover
both message and callback handlers, the real shared photo sender and keyboard,
HTTP and Telegram fallback, unexpected errors, cancellation, and fallback failure.
Every remaining legacy prefix and the generic route have dispatch checks.
`bot/tests/handlers/test_feed_specialized_processors.py` covers the migrated media
sources, their literal callback payloads, and source-specific rendering branches.

The registry builds on exception prerequisite commit
`6123f94fbfd2c169df27c336becb853b46ea1fd8`, published in
[PR #26](https://github.com/gakawarstone/gkbot/pull/26).
