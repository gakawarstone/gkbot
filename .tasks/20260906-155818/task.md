# Bound middleware user data retention

- STATUS: OPEN
- PRIORITY: 2

## Problem

`UserDataMiddleware` stores per-user dictionaries in a class-level mapping with no TTL, size bound, or cleanup path. Entries can retain messages and delete queues for the lifetime of the process, then disappear on restart.

## Plan

1. Inventory the values stored in middleware user data and their required lifetime.
2. Add a bounded retention policy suitable for active FSM sessions.
3. Remove entries when sessions finish and expire abandoned entries.
4. Avoid deleting state that an active handler still uses.
5. Add tests for expiry, explicit cleanup, and active-session retention.

## Acceptance criteria

- Per-user data has a documented lifetime and a working cleanup path.
- Storage cannot grow without a configured bound.
- Active flows retain their data until completion.
- Middleware tests and static checks pass.

