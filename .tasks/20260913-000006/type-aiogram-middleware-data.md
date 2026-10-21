# Type aiogram middleware data

- STATUS: OPEN
- PRIORITY: 2

## Problem

Project middleware adds user data, timezone, state, and delete queues to an untyped dictionary. Handlers access these values by string key, so missing keys and incompatible values reach runtime despite mypy and pyright checks.

## Plan

1. Inventory every value written to and read from aiogram middleware data.
2. Define a project `MiddlewareData` type that extends aiogram's typed middleware context.
3. Type middleware call signatures and injected handler dependencies.
4. Replace broad `dict` and `Any` annotations where the actual contract is known.
5. Add type-checking fixtures for required and optional context values.

## Acceptance criteria

- Custom middleware keys and value types have one declared contract.
- Handler and middleware code no longer casts or guesses common injected values.
- Missing or wrongly typed context values fail static checks.
- mypy, pyright, Ruff, and unit tests pass.

