# 01: Remove unused configuration hooks

**What to build:** Remove confirmed configuration fields and method parameters that have no runtime consumer, without changing bot behaviour.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] The unused administrator field is no longer carried through bot configuration.
- [ ] The unused request-body parameter is removed from the feed API helper and all callers still work.
- [ ] Focused tests and static checks pass without compatibility shims for the removed hooks.
