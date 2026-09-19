# 02: Introduce typed startup hooks

**What to build:** Represent synchronous and asynchronous startup work as one explicit, typed concept while preserving execution order and failure behaviour.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] Bot configuration carries one startup-hooks value instead of two parallel collections.
- [ ] Both synchronous callbacks and asynchronous work execute in the documented order.
- [ ] Tests cover mixed hook execution and propagation of a failing hook.
