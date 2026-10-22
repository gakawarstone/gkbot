# Separate the Pomodoro restart confirmation from handler state

- STATUS: OPEN
- PRIORITY: 4

## Problem

`bot/handlers/user/road/pomodoro/restart.py` stores a live handler in user data as `callback`, mutates the delete queue, and changes the road FSM. Moving this file into extensions alone would leave those dependencies intact.

## Acceptance criteria

- Inventory callers of `ask_to_restart` and `choose_bool` and document the state and cleanup behavior they need.
- Extract a confirmation helper that receives the action and state transitions explicitly instead of depending on road-specific keys and FSM values.
- Test yes, no, repeated input, and message cleanup without calling the action twice.
- Remove the move-to-extensions marker only after callers use the new helper.
