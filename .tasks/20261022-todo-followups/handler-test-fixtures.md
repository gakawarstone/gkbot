# Make feed and Pomodoro handler test inputs explicit

- STATUS: OPEN
- PRIORITY: 4

## Problem

`bot/tests/handlers/test_feed.py` rotates through hidden mutable `LINKS` state in a mocked picker. `bot/tests/handlers/test_pomodoro.py` assumes one button per row and uses the same numeric message for every setting. These three markers concern test design rather than production behavior.

## Acceptance criteria

- Parameterize feed cases by URL and give the mocked picker its case's URL explicitly.
- Iterate actual button objects across every keyboard row without assuming a one-button layout.
- Give each Pomodoro setting an explicit valid input and expected stored value.
- Add invalid numeric input coverage and verify that stored settings do not change.
- Keep network-dependent feed tests opt-in and run deterministic Pomodoro checks offline.
