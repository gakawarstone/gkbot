# Return downstream results from middleware

- STATUS: OPEN
- PRIORITY: 1

## Problem

Several middleware classes await the downstream handler but discard its result despite declaring an `Any` return type. This breaks the middleware contract and can discard webhook responses.

## Plan

1. Audit `RegisterUserMiddleware`, `UserDataMiddleware`, `DeleteQueueMiddleware`, `TimeZoneMiddleware`, and `NotEnoughRightsMiddleware`.
2. Return the downstream result on every successful path.
3. Keep intentional short-circuit paths explicit and typed.
4. Add a parameterized test that verifies result propagation for each middleware.

## Acceptance criteria

- Every successful middleware path returns `await handler(event, data)` or its stored result.
- Short-circuit behavior is covered by tests.
- Middleware tests, mypy, and Pyright pass.

