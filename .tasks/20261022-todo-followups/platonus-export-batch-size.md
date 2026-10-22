# Make the Platonus export batch size explicit

- STATUS: OPEN
- PRIORITY: 4

## Problem

`bot/handlers/user/platonus2indigo/convert_file.py` passes a literal 25 to `get_lines_with_max_questions`. This is the current export default, not a verified Indigo format limit. The converter already accepts a batch size; the handler exposes no choice.

## Acceptance criteria

- Name and document the current default of 25 questions per output file.
- If exposing a user setting, validate a positive batch size and define how it is stored and selected before changing the interaction.
- Test 25 and 26 questions, ensuring each question appears once, output filenames remain distinct, and the final partial file is emitted.
