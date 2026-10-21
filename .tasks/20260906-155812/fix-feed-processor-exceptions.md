# Replace broad feed processor exception handling

- STATUS: OPEN
- PRIORITY: 1

## Problem

`GkfeedItemProcessorExtension._process_item` catches every `Exception`, silently falls back to a plain link, and prints a vague message. Programming errors such as missing methods are hidden as ordinary content failures.

## Plan

1. Identify the expected extraction, network, and Telegram exceptions for feed views.
2. Catch only recoverable exceptions and keep the plain-link fallback for those cases.
3. Log the item identifier, processor name, and exception with the project logger.
4. Let unexpected programming errors propagate.
5. Add tests that distinguish recoverable failures from programming errors.

## Acceptance criteria

- `_process_item` has no blanket `except Exception` fallback.
- Recoverable media failures still send a plain link.
- Unexpected errors fail visibly and retain their traceback.
- Focused tests and static checks pass.

