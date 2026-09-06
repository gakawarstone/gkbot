# Remove deprecated Piokok integration

- STATUS: OPEN
- PRIORITY: 1

## Problem

The Piokok feed integration is marked as deprecated and no longer works, but it is still imported, selected by the feed processor, and registered as a callback handler. It also contains an invalid `_gkfeed()` call.

## Plan

1. Remove the Piokok feed view from the processor inheritance tree and URL dispatch table.
2. Remove the Piokok callback registration and its keyboard implementation.
3. Delete Piokok-only modules after confirming that no shared code depends on them.
4. Update affected feed tests.

## Acceptance criteria

- No runtime route, processor, callback, or keyboard references Piokok.
- The remaining feed handlers import and initialize successfully.
- Relevant tests, Ruff, mypy, and Pyright pass for the changed files.
