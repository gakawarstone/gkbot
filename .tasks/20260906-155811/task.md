# Fix GKFeed access in Stories

- STATUS: OPEN
- PRIORITY: 1

## Problem

`StoriesFeedItemView` calls `self._gkfeed()`, but no class in its inheritance chain defines that method. Pyright reports the missing attribute, and the generic feed fallback hides the runtime failure.

## Plan

1. Replace the invalid call with the supported `GkfeedApi` construction path using the handler credentials.
2. Add a focused test for processing a Stories item and retrieving its raw feed data.
3. Keep authentication and API errors visible to the caller.

## Acceptance criteria

- Stories processing does not reference `_gkfeed()`.
- A test covers the successful API call and a failed API call.
- Pyright reports no error for `views/stories.py`.

