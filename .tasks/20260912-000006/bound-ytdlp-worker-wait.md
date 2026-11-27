# Bound yt-dlp worker polling

- STATUS: OPEN
- PRIORITY: 2

## Problem

`bot/workers/yt_dlp.py` polls until a task reports exactly `completed`. A failed, cancelled, unknown, or permanently queued task keeps the Telegram handler waiting forever. The loop has no deadline and does not expose the worker's failure result.

This task depends on the worker protocol decision in `.tasks/20260906-155817/decide-youtube-worker-contract.md`.

## Plan

1. Record the terminal success and failure statuses from the selected worker protocol.
2. Add a configurable overall deadline and a bounded polling interval.
3. Raise a specific exception for failed tasks, malformed responses, and timeouts.
4. Map those exceptions to a useful user-facing download error and preserve diagnostic context in logs.
5. Add tests for completion, failure, cancellation, malformed status data, and timeout.

## Acceptance criteria

- Polling ends for every terminal worker status.
- A task that never reaches a terminal state stops at the configured deadline.
- Callers receive specific exceptions rather than waiting forever.
- User-facing handlers clean up their status messages and report the failure.
- Focused worker and handler tests pass.

## Implementation checkpoint, 2026-10-31

Blocked pending owner selection in [contract PR #30](https://github.com/gakawarstone/gkbot/pull/30),
currently draft at `0aec7cefa9cc40ba10488441f95620db3bd81140`, and the verified
shared payload helper. No runtime changes are authorized until these are ready.
This task remains OPEN; this checkpoint is preparation, not completed work.

Dependencies:

- Contract: thread `mcp:9f7cfb57-c3b1-4322-b7f9-58a34d8c47f2`, branch
  `task-20261022-decide-youtube-worker-contract`.
- Shared helper: thread `mcp:f23bc244-c5c7-4e80-a5a5-b29b576228ce`, branch
  `task-20261023-19-share-ytdlp-worker-payload-fetching`. No helper PR yet.

The proposed external broker stores `pending`, `processing`, `completed`, and
`failed`. Cancellation removes a pending task and GET returns 404. The legacy
worker can encode a failure inside a JSON string result with outer status
`completed`. These rules and exception names are still proposals. Production
bot/broker pairing remains unverified. Use the approved policy and helper
contract when delivered, without duplicating payload retrieval or validation.

### Implementation and tests after approval

Code inspected at `dfdecceb2e97824e924538bf7720c2547a7156a7`:

- Polling requests status twice before sleeping, sleeps after completion, and
  fetches the result again. Consume the shared helper's terminal payload once.
- Propose a configurable 300-second deadline per worker operation and a
  1-second interval, both finite and positive. Bound enqueue, HTTP requests,
  and sleeps by one monotonic deadline. A user action can perform separate
  metadata and download operations.
- Reuse shared exceptions for protocol, unavailable, and failed tasks. Add
  timeout handling and operation decoding, including embedded legacy failure.
  Let local cancellation propagate. Log task/operation/error context without
  sending raw worker payloads to users.
- YouTube audio/video callbacks and Shorts delete progress messages only on
  success. Catch typed worker errors, report a useful Russian error, and clean
  up in `finally`, including metadata failures before the context manager
  yields. Cleanup errors must preserve the original failure.

Add unit tests with mocked enqueue/helper calls and controlled time:

- Immediate and delayed success, no extra GET or sleep after completion.
- Every approved terminal failure and embedded failure; propagate helper
  malformed/unavailable errors without duplicating its parser tests.
- Invalid operation results, including malformed metadata JSON.
- Permanently pending tasks and stalled enqueue/GET stop at the deadline;
  sleeps cannot extend it. Invalid configuration fails deterministically.
- Caller cancellation propagates. YouTube audio/video and Shorts report typed
  failures, send no media, log diagnostics, and remove progress messages.
  Cover callback-message reuse, metadata/download errors, media-send failures,
  and cleanup failure preserving the primary exception.

Run focused worker/handler `make test FILE=...` and changed-file
`make lint FILE=...` after implementation. Existing handler integration tests
are skipped by ordinary `make test`; new unit coverage is needed. No Python
changes or runtime test execution are part of this preparation PR.
