# Move habit creation into a service with validated input

- STATUS: OPEN
- PRIORITY: 4

## Problem

`bot/handlers/user/road/habits/__init__.py` writes directly through `Habits.create`. Its marker does not say which behavior the replacement should preserve. The handler also parses notification time with `datetime.strptime` without handling invalid input.

## Acceptance criteria

- Put habit persistence behind a small service or repository and remove the handler's model import.
- Validate a nonempty habit name and an HH:MM notification time before saving.
- Keep the current FSM step and send a retry prompt for invalid input.
- Test the stored user ID, name, and time, plus rejected input and absence of writes on rejection.
