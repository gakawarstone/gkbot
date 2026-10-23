# Middleware data contract

`middlewares.data.MiddlewareData` extends the TypedDict shipped with aiogram
3.31.0. `UserData` describes the nested `data` argument injected into project
handlers. Do not annotate that argument as the outer `MiddlewareData`.

## Injection stages

- Aiogram supplies `bot`, dispatcher/update/router/handler metadata and FSM
  values. Their types come from aiogram's base contract. `state` is optional
  because userless updates do not necessarily have an FSM context.
- `BotStarter` supplies `admins: list[int]` through dispatcher workflow data.
  `BotAdmin`, startup and error handlers consume it.
- `RegisterUserMiddleware` checks the event's user and registers it. It adds no
  context keys. Inline queries only pass through this project middleware.
- `UserDataMiddleware` installs `data: UserData` for messages and callbacks.
  The outer key is optional before this stage. `require_user_data(context)`
  checks its presence and returns the typed value.
- `TimeZoneMiddleware` writes `data["tz"]` for messages whose selected handler
  has `require_timezone`. It stops handling when the user has no timezone.
- `DeleteQueueMiddleware` drains `data["delete_queue"]` on messages.
  `NotEnoughRightsMiddleware` adds no keys and preserves downstream results.

The upstream context also carries flag metadata in `handler`. The project
boolean filters do not add context entries. Button handlers declare their own
button-specific payload types; those are outside the shared user cache.

## User cache inventory

`delete_queue: list[Message]` is required. UserDataMiddleware initializes it to
an empty list for a new user, including a first callback update. One-time message
extensions and the pomodoro restart flow append messages. DeleteQueueMiddleware
consumes the pending batch before the next message handler runs.

All remaining keys may be absent. Fields managed by the legacy context manager
can also be reset to `None`.

- `tz: timedelta | None`: timezone middleware and reminder context write it;
  timezone-dependent handlers and reminder creation read it.
- `callback: RestartableHandler`: the pomodoro restart prompt saves a handler;
  the yes/no step calls it again. The protocol specifies `event`, `state`,
  `user_data`, and async `handle`.
- `habit_name: str | None`, `habit_notify_time: time`: the habit conversation
  writes these before creating a habit.
- `messages: list[str] | None`: the ChatGPT conversation keeps prompt and reply
  history.
- `file_name: str | None`: the document-download conversation stores a filename.
- `text: str | None`, `date: date | None`, `time: time | None`,
  `message: Message | None`: the reminder conversation stores text, schedule and
  its editable summary. The add-book conversation also uses `message`.
- `name: str | None`, `author: str | None`, `chapter_cnt: int | None`: the
  add-book conversation stores book details.
- `property_name: str | None`, `new_value: str | None`, `book_id: int | None`:
  the edit-book conversation stores the selected property, value and book.
- `setting_name: str | None`, `setting_new_value: time | None`: the road settings
  conversation stores its selected setting and parsed time value.

These remain ordinary dictionaries at runtime. Message and callback middleware
share one bounded, dispatcher-owned `UserDataStore`, currently keyed by Telegram
user ID across chats. New entries include `delete_queue: []`; the dictionary
stays pinned while handlers use it. Final FSM completion releases context,
retaining only pending deletions, and idle expiry releases abandoned entries.
See [the retention contract](user-data-retention.md) for limits and stale FSM
reset. Tests inject a fresh store instead of patching class-level storage;
`test_data.py` demonstrates sharing within one active session.

## Handler access and boundaries

Function handlers annotate their injected argument as `data: UserData`, and
FSM dependencies as `state: FSMContext`. Message and callback class handlers
share a typed base constructor and `user_data`/`state` properties. A handler
that does not use these dependencies can omit them when instantiated directly;
accessing an omitted dependency raises an explicit error. The `tz` property
checks for an available offset and returns `timedelta`.

Use `.get()` or a membership check for optional keys before consuming them.
Pyright rejects unguarded optional-key indexing. Mypy permits that indexing,
but both reject assigning an unchecked `.get()` result to a non-optional type.
Both reject a missing required queue, unknown keys, incompatible values and
wrongly typed constructor dependencies.

The legacy dataclass context manager accepts runtime field names and validates
values against reflected annotations. Its dynamic writes use one explicit
`MutableMapping[str, Any]` boundary. Replacing that API belongs to the separate
context-manager task. Common injected values do not pass through that cast.
Aiogram's arbitrary downstream result and extra framework constructor kwargs
also retain `Any` at framework boundaries.

Middleware overrides have narrowly scoped mypy/pyright suppressions because
aiogram's BaseMiddleware uses `dict[str, Any]`, which a TypedDict cannot override
under substitution rules. This is the incompatibility described in
[aiogram's dependency injection documentation](https://docs.aiogram.dev/en/v3.31.0/dispatcher/dependency_injection.html#using-type-hints).
Flag lookup receives a plain shallow dictionary copy for the same reason.

The timezone extension declares aiogram's `aiogram_flag` attribute directly.
The flag decorator's return annotation erases class types, so using it here
would hide the extension's typed dependencies from checkers.

## Verification

Run the runtime and static contract regressions together:

```sh
make test FILE=bot/tests/middlewares
```

`test_data_typing.py` runs mypy and pyright against positive and intentionally
invalid fixtures in `typing_tests/middleware_data`. Every marked invalid line
must produce an error in each checker. Those files live outside `bot/` so
regular linting does not include expected failures. The test configures import
paths and uses mypy's silent imported-module diagnostics to isolate the fixture
from unrelated repository errors.

A focused check of the production middleware contract is:

```sh
make lint FILE=bot/middlewares
```

At the starting revision, full `make lint` stopped at 383 Ruff findings. Full
mypy and pyright each reported two existing errors: a Message mock's `__class__`
assignment and media-group list invariance in `handlers/prompt/generate_image.py`.
The mock was updated with the typed middleware tests. The image-generation
error is outside this task and remains in full-repository type checks.
