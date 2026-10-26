# 05: Consolidate the TikTok extractor contract

**What to build:** Give TikTok extractors one shared path for constructing video information and translating expected extraction failures, leaving each provider responsible only for obtaining provider-specific data.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] Provider implementations no longer repeat the default video-information construction.
- [ ] Expected provider failures are exposed through one consistent exception contract.
- [ ] Contract tests run against every migrated extractor.
