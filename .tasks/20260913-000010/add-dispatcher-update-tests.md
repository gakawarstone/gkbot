# Add dispatcher-level update tests

- STATUS: OPEN
- PRIORITY: 2

## Problem

Most handler tests call handlers directly. They do not prove that routers, filters, middleware injection, FSM state, and error handling work together for a raw Telegram update. Aiogram documents `Dispatcher.feed_raw_update` as a focused integration-test path.

## Plan

1. Add a dispatcher test fixture with the production router and middleware setup.
2. Feed representative raw updates for a command, callback, inline query, and FSM transition.
3. Record outbound Bot API calls without network access.
4. Cover an exception path through the registered error handler.
5. Keep direct unit tests for handler internals.

## Acceptance criteria

- Tests prove that representative raw updates reach the intended handlers.
- Middleware data and FSM state are present at handler invocation.
- Unexpected updates do not trigger unrelated handlers.
- The tests make no external Telegram or service calls.

