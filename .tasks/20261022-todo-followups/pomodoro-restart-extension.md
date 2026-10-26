# Review the Pomodoro restart confirmation lifecycle

- STATUS: OPEN
- PRIORITY: 4

## Problem

`bot/handlers/user/road/pomodoro/restart.py` stores a live handler in user data as `callback`, mutates the delete queue, and changes the road FSM. Its only caller is `PomodoroHandler`. The move-to-extensions marker does not justify a shared confirmation abstraction.

## Acceptance criteria

- Keep the confirmation local to Pomodoro while it has one caller.
- Ensure yes restarts once, no does not restart, and confirmation messages are cleaned up; cover repeated input without calling the action twice.
- Release the stored handler when confirmation ends so user data does not retain the completed interaction.
- Replace the move-to-extensions marker with a description of the local lifecycle once verified.
