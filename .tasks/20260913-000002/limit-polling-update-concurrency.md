# Limit polling update concurrency

- STATUS: OPEN
- PRIORITY: 1

## Problem

`BotStarter` calls `Dispatcher.start_polling()` without `tasks_concurrency_limit`. Each update can become a separate task, while handlers perform AI streaming, media downloads, album processing, and image generation. A burst of updates can exhaust memory or saturate external services.

## Plan

1. Measure handler throughput, peak memory, and external service limits under concurrent updates.
2. Add a configurable polling concurrency limit with a conservative default.
3. Pass the limit to `Dispatcher.start_polling()` while retaining task-based update handling.
4. Document how to tune the limit for production.
5. Add a focused test that verifies the configured value reaches the dispatcher.

## Acceptance criteria

- Polling has a finite, configurable update-task limit.
- The default does not serialize all updates or exceed measured resource limits.
- Configuration validation rejects non-positive values.
- Polling tests and static checks pass.

## Progress on 2026-10-23

Implemented environment configuration, positive-integer validation, explicit
task-based polling, and dispatcher forwarding tests. The existing default of
10 is retained. See `docs/polling-concurrency.md` and
`bot/benchmarks/polling.py` for the reproducible offline `/img` burst benchmark.
At limit 10 it measured 10 active updates, 40 simulated provider requests,
200.60 MiB traced peak allocation, and 448.17 MiB process peak RSS.

Checks: 144 tests passed, 13 skipped. `make lint FILE=...` passes for all seven
changed Python files. Full lint still reports 377 existing Ruff findings,
compared with 383 on the starting HEAD.

The production resource acceptance criterion remains open. The offline
benchmark does not establish live handler throughput or deployed account
quotas. To finish, measure the representative production/staging workload
against its memory budget and provider limits, then confirm or lower the
default. Alternatively, the owner can explicitly accept 10 as a starting
default backed by the offline measurement and defer deployment-specific
calibration to rollout. Keep this task until that decision or measurement.

