# Isolate failures in the schedule dispatcher

- STATUS: OPEN
- PRIORITY: 1

## Problem

`Schedule.__dispatcher` awaits each task without handling task-level errors. One failed reminder or cache cleanup exits the only dispatcher loop, so every later scheduled task remains in the database until the bot restarts.

## Plan

1. Catch task execution errors inside the per-task loop and log the task ID with its traceback.
2. Define whether a failed task is removed, retried, or marked failed, with a bounded retry policy.
3. Keep processing other due tasks after one task fails.
4. Retain and cancel the dispatcher task during shutdown so background errors remain visible.
5. Add tests with failing and successful tasks due in the same dispatcher pass.

## Acceptance criteria

- A failed task does not stop the dispatcher or prevent another due task from running.
- Failed tasks follow a documented, bounded retry or removal policy.
- Dispatcher failures are logged with the stored task ID and traceback.
- Startup and shutdown manage the dispatcher task explicitly.
- Focused schedule tests pass.

