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

