# Delete the undiscovered example test

- STATUS: OPEN
- PRIORITY: 3

## Problem

`bot/tests/handlers/example.py` is outside normal pytest discovery. Its fake handler does nothing, and its test has no assertion, so the file provides no coverage even when run directly.

## Plan

1. Confirm that no fixture or test imports `example.py`.
2. Delete the file rather than renaming a no-op test into discovery.
3. Run test collection and the handler test suite.

## Acceptance criteria

- `example.py` is removed.
- Test collection contains no reference to its fake handler.
- The handler test suite passes with the same meaningful coverage.

