# Prevent poison messages from blocking the delete queue

- STATUS: OPEN
- PRIORITY: 1

## Problem

`DeleteQueueMiddleware` clears a user's queue only after every queued message is deleted. One failed Telegram deletion leaves the same message in the queue and makes later updates retry the failing item indefinitely.

## Plan

1. Detach or clear the queued batch before attempting Telegram deletions.
2. Replace the side-effect list comprehension with an explicit loop.
3. Define handling for already deleted, inaccessible, and unauthorized messages.
4. Preserve new queue entries added while the detached batch is processed.
5. Add tests for partial failure and a subsequent update.

## Acceptance criteria

- One failed deletion does not block later queue processing.
- New entries are not lost during cleanup.
- Expected Telegram deletion errors follow an explicit policy.
- Middleware tests and static checks pass.

