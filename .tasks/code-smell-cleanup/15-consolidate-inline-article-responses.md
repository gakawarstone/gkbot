# 15: Consolidate inline article responses

**What to build:** Provide one helper for answering an inline query with a single generated article while leaving each command responsible for its content.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] Chance, list choice, and joke handlers share article ID generation and response construction.
- [ ] Each handler retains its current title, message, description, and cache policy.
- [ ] Tests cover the shared response contract and one content-specific case per handler.
