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

