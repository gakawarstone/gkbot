# 10: Add a feed processor registry

**What to build:** Add a registry in parallel with the existing feed processor hierarchy and route one representative source through it as an end-to-end tracer bullet.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] A processor entry owns both source matching and item handling.
- [ ] One representative source is selected and rendered through the registry with unchanged fallback behaviour.
- [ ] Existing processors continue to work during migration.
