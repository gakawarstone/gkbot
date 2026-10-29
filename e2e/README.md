# Testgram scenarios

Run `make e2e` for smoke scenarios or `make e2e-live` for the reported TikTok URL.
The live post is sensitive and may require cookies or fallback extractors.

Testgram has no deterministic TikTok fixtures or upload byte-size assertion.
Its 50 MiB request limit does not verify the bot's 15 MiB compression policy;
use the local regression tests for that policy.
