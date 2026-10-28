# Simple feed processor contract

Each source module in `modules.feed.handlers.processors` exports
`create_<source_id>_processor(...) -> FeedProcessor`. Stable source IDs are
`kinogo`, `spoti`, `rezka`, `shiki`, `telegram`, `hltv` and `twitch`.

Rendering dependencies are passed explicitly:

- Kinogo, Spotify, Rezka and Telegram take `send_photo` and `send_item`.
- Shikimori and Twitch take `send_photo`.
- HLTV takes `answer_photo` for a buffered upload and `send_item`.

Callback protocols are defined in `processors._simple_rendering`. Its shared
HTML fetch helper retains `HttpService.headers` for Kinogo, Spotify and
Shikimori; replacing it with Open Graph fetching would change those headers.

Matchers retain the original URL prefixes, including longer hostnames starting
with those prefixes. Task 13 owns URL-filter changes. Matching performs no
network requests. Entries follow the [registry contract](feed-processor-registry.md)
and [shared failure policy](feed-processor-exceptions.md).
