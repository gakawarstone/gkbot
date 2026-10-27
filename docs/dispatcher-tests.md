# Dispatcher update tests

`bot/tests/dispatcher` feeds raw Telegram dictionaries through
`Dispatcher.feed_raw_update`. Each test uses fresh FSM memory storage and the
production `middlewares.setup`, `handlers.setup`, and `modules.setup` functions,
in the same order as `BotStarter`. Existing direct handler tests remain useful
for internal branches and service behavior.

Run the dispatcher tests and their static checks with:

```bash
make test FILE=bot/tests/dispatcher
make lint FILE=bot/tests/dispatcher
```

## What the tests prove

- A raw `/set_tz` command selects the registered command handler and injects a
  real FSM context and per-user data. A subsequent numeric message selects the
  state handler, persists the offset through the service boundary, and advances
  the state. Invalid text retries; another user's numeric message is unhandled.
- `/add_remind` receives the timezone inserted by the flagged middleware, along
  with its user data and FSM context. Without a timezone, middleware prompts for
  `/set_tz` before the handler runs and leaves the FSM unchanged.
- `/tts` starts a conversation and queues its prompt for deletion. `/exit`
  takes precedence over the active state handler, flushes that queue, and clears
  the FSM without invoking speech synthesis.
- A raw delete-message callback selects the production callback handler and
  deletes the referenced message. Its injected data is the same object used by
  an earlier message from that user, while the FSM remains active.
- A raw inline choice query selects the production inline handler, runs user
  registration, and answers the original query ID with the expected article.
- A persistence exception propagates through the registered error handler,
  which sends a traceback document and user details to each configured admin.
- Unmatched text, command, callback, and inline updates return `UNHANDLED` with
  no handler invocation, persistence writes, or outgoing Bot API methods.

An observing inner middleware records the selected production callback and its
injected dependencies immediately before invocation. It then calls the original
handler. Assertions check both those observations and resulting Bot API methods
or FSM changes.

## Offline boundaries

The recording `BaseSession` handles only message/document sends, message
deletion, and inline answers. It records concrete `TelegramMethod` objects and
returns local models or booleans. Unsupported methods and file downloads fail
the test. Socket connections and DNS resolution also fail immediately, using
`pytest.fail` so the production error handler cannot swallow a guard failure.

The fixture replaces `Users.filter(...).first`, `Users.create`, and timezone
service reads/writes with local mocks. Router registration, filters, middleware,
FSM storage, and handlers run unchanged. It never runs startup hooks, polling,
notifier setup, or background workers. Teardown closes FSM storage and session.

## Prerequisite integration

The PR uses `task-20261023-dispatcher-prerequisites` at
`81ee096f68f42797488e10871cf64ca485a8948c` as its review base. The conflict
coordination wave 20261025, with the middleware simplification of 20261027,
combines the published Notion removal head
`60c31beb8f716ff51845d99613b2fd28f280b1f6`, command registry head
`f90615c21e9e6860274865c54bc7d0e1d878cb33`, and middleware typing head
`162e7efc5a6d9329951aa3cfe33cf1411f6b67b7`. All include the selected
`dev-3.0` snapshot `2db43ed99af695c841ed7c29194df88da8d42225`.
Ordinary merges preserve the registry, typed context, import ordering, and
agreed test deletions. After PRs #25, #40, and #41 merge, retarget the test PR
to `dev-3.0` and verify its diff again. No prerequisite PR is merged by this work.

This combination uses the typing-only user-data cache. The fixture replaces
`UserDataMiddleware._UserDataMiddleware__data` with a fresh dictionary for each
test and restores it afterwards. Retention PR #37 is a separate change; when
integrating it, adapt the fixture to a fresh `UserDataStore` and share that store
between message and callback middleware. Do not restore the removed class cache.

The aiogram [testing guide](https://docs.aiogram.dev/en/latest/dispatcher/testing.html)
and [dispatcher reference](https://docs.aiogram.dev/en/latest/dispatcher/dispatcher.html#aiogram.dispatcher.dispatcher.Dispatcher.feed_raw_update)
document the raw-update entry point used here.
