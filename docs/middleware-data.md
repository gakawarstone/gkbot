# Middleware data contract

`middlewares.data.MiddlewareData` extends the TypedDict shipped with aiogram
3.31.0. The nested `data` argument is an extensible internal dictionary;
conversation fields are defined by their own `ContextField` schemas.

## Injection stages

- Aiogram supplies `bot`, dispatcher/update/router/handler metadata and FSM
  values. Their types come from aiogram's base contract. `state` is optional
  because userless updates do not necessarily have an FSM context.
- `BotStarter` supplies `admins: list[int]` through dispatcher workflow data.
  `BotAdmin`, startup and error handlers consume it.
- `RegisterUserMiddleware` checks the event's user and registers it. It adds no
  context keys. Inline queries only pass through this project middleware.
- `UserDataMiddleware` installs `data: dict[str, Any]` for messages and callbacks.
  The outer key is optional before this stage. `require_user_data(context)`
  checks its presence and returns the typed value.
- `TimeZoneMiddleware` writes `data["tz"]` for messages whose selected handler
  has `require_timezone`. It stops handling when the user has no timezone.
- `DeleteQueueMiddleware` drains `data["delete_queue"]` on messages.
  `NotEnoughRightsMiddleware` adds no keys and preserves downstream results.

The upstream context also carries flag metadata in `handler`. The project
boolean filters do not add context entries. Button handlers declare their own
button-specific payload types; those are outside the shared user cache.

## Handler access and boundaries

Function handlers annotate their injected argument as `data: dict[str, Any]`, and
FSM dependencies as `state: FSMContext`. Message and callback class handlers
share a typed base constructor and `user_data`/`state` properties. Their base
keeps `context` as a reference to aiogram's injection dictionary. One cast at
that framework boundary avoids storing a second copy of `data` and `state`.
A handler that does not use these dependencies can omit them when instantiated
directly. Accessing an omitted dependency raises an explicit error. The `tz` property
checks for an available offset and returns `timedelta`.

Use `.get()` or a membership check for optional middleware dependencies. Both
checkers reject incompatible middleware and constructor dependencies. The
internal user dictionary intentionally has no exhaustive key schema.

The context manager uses typed `ContextField` descriptors and validates their
values against the declared schema. It writes dynamic field names to the
internal user dictionary.
Aiogram's arbitrary downstream result and extra framework constructor kwargs
also retain `Any` at framework boundaries.

Middleware overrides have narrowly scoped mypy/pyright suppressions because
aiogram's BaseMiddleware uses `dict[str, Any]`, which a TypedDict cannot override
under substitution rules. This is the incompatibility described in
[aiogram's dependency injection documentation](https://docs.aiogram.dev/en/v3.31.0/dispatcher/dependency_injection.html#using-type-hints).
Flag lookup reads the selected `HandlerObject` directly from the context.

The timezone extension uses aiogram's `require_timezone` decorator. A cast at
the decorator boundary preserves the class type for static checkers.

## Verification

Run the runtime and static contract regressions together:

```sh
make test FILE=bot/tests/middlewares
```

`test_data_typing.py` runs mypy and pyright against intentionally invalid uses
of the project injection contract in `typing_tests/middleware_data/invalid.py`.
Every marked line must produce an error in each checker. The fixture lives
outside `bot/` so regular linting does not include expected failures. The test
configures import paths and uses mypy's silent imported-module diagnostics to
isolate the fixture from unrelated repository errors.

A focused check of the production middleware contract is:

```sh
make lint FILE=bot/middlewares
```
