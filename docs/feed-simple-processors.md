# Simple feed processors

Kinogo, Spotify, Rezka, Shikimori, Telegram, HLTV and Twitch now render through
standalone source factories in `modules.feed.handlers.processors`. Their inherited
views and legacy dispatch entries have been removed. The registry implementation
and shared exception policy are unchanged.

## Ownership

Task 11 owns Kinogo, Spotify, Rezka, Shikimori, Telegram, HLTV and Twitch.
Task 10 owns Discours as its first registered source.
Task 12 owns Stories, VK, YouTube, Reddit, TikTok, Pornhub, Porno365,
Instagram, Sasflix, Matreshka and the video helper.
Task 13 owns removal of the combined processor hierarchy and the remaining
central URL-prefix dispatch.

Each source module declares its own matcher and `create_<source_id>_processor`
factory returning a `FeedProcessor`. Stable identities are `kinogo`, `spoti`,
`rezka`, `shiki`, `telegram`, `hltv` and `twitch`. Each entry binds its matcher
and asynchronous processing callback. See the
[registry contract](feed-processor-registry.md) for ordered resolution and
[exception policy](feed-processor-exceptions.md) for execution failures.

The composition property supplies shared rendering callbacks explicitly:

- Kinogo, Spotify, Rezka and Telegram take `send_photo` and `send_item`.
- Shikimori and Twitch take `send_photo`.
- HLTV takes `answer_photo` for a buffered upload and `send_item`.

`processors._simple_rendering` defines callback protocols and the HTML fetch
helper used by Kinogo, Spotify and Shikimori. That helper retains the previous
`HttpService.headers` request headers. Factories never inherit feed views or
perform network requests during construction or matching.

Matchers retain the original URL prefixes, including acceptance of longer
hostnames starting with those prefixes. URL validation changes belong to task 13.
Adding another source requires its factory and an entry in the composition
property, without changing registry internals or processor inheritance.

## Rendering and fallback cases

| Source | Existing rendering to preserve | Cases to cover |
| --- | --- | --- |
| Kinogo | First `link` element's `href`, empty description | Missing link or href sends the generic item |
| Spotify | Twitter image/title/description metadata; playlists use their title; releases use release and artist names | Missing image, title or description sends the generic item; cover playlist and release captions |
| Rezka | Preview request changes host to `rezka.ag`, retains path/query and uses TelegramBot header; photo caption uses the feed title | Missing image sends the generic item; assert preview URL and headers |
| Shikimori | Poster image, itemprop image, picture srcset or Open Graph image; normalize protocol-relative URLs; title before slash | Exercise each image selector, title extraction and invalid markup through the registry's failure policy |
| Telegram | Open Graph image and description, truncated to 250 characters | Missing image or description sends the generic item; test boundary and truncation |
| HLTV | Download image with HTTP-to-HTTPS normalization; caption includes escaped matchup and optional match time | Missing image sends the generic item; malformed event JSON keeps matchup without time; preserve buffered upload |
| Twitch | Channel thumbnail, feed text or title, channel name as link caption | Preserve channel extraction and failure on missing channel |

## Regression coverage

- Resolve each source through the real registry, then assert the rendered
  message or photo using mocked HTTP and Telegram calls.
- Verify common feed navigation with actual markup generation. Keep/delete
  callbacks retain the item ID, and show-all-feed retains the feed ID.
- Exercise both message and callback-query delivery through shared rendering.
- Confirm photo rejection still invokes the generic feed-item fallback.
- Apply the exception policy supplied by task 10 and its prerequisite. Do not
  add broad exception catches in individual source modules.

`bot/tests/handlers/test_feed_simple_processors.py` implements these checks with
offline HTML and image fixtures. Assertions inspect the outgoing media, captions,
original fallback links and navigation payloads. Shared failure and cancellation
checks use representative URL-photo and buffered-upload paths rather than
repeating every source. The existing legacy-dispatch and exception tests have
been adapted to the migration. `bot/tests/handlers/test_feed.py` remains an integration test
skipped in the ordinary offline run.

After integrating the updated registry parent, the full `make test` run passed
with 262 passed and 13 skipped. File-scoped `make lint` and format checks passed
for the processors, composition and relevant test modules. No removed mirror
tests were restored.

## Integration base

This migration builds on registry commit
`d59f8c789c144244dba0237793346c836cfb28e2`, published in
[PR #46](https://github.com/gakawarstone/gkbot/pull/46), and exception prerequisite
`6138b0c322bcadee1ad7a9f4c004f148c80a578f`. Task 12 merges this migration and
combines both sets of entries in `_processor_registry`, retaining the original
source order and shared rendering behavior. Task 13 removes the empty legacy map
and remaining aggregate inheritance and owns the matching-filter follow-up.
