# Evaluate Telegram keyboard visual styles

- STATUS: OPEN
- PRIORITY: 4

## Problem

Newer Bot API versions support button styles and custom emoji icons. The current keyboard system uses text and standard Unicode emoji. A broad visual rewrite would add complexity without proving that it helps users.

## Plan

1. Choose one frequently used keyboard and define a small visual experiment.
2. Verify bot eligibility and client support for custom emoji icons.
3. Compare styled and current keyboards for clarity, accessibility, and fallback rendering.
4. Centralize any accepted style choices in keyboard helpers.
5. Stop after the experiment if the change is only decorative.

## Acceptance criteria

- The experiment has before and after screenshots on supported clients.
- Buttons remain understandable when styles or custom emoji are unavailable.
- Accepted styles use shared helpers instead of per-handler constants.
- The task records a keep or reject decision.

## Evaluation update, 2026-10-23

See [the experiment report](../../docs/keyboard-visual-style-experiment.md).
The bounded candidate adds `danger` only to the YouTube dialog's `убрать`
button and preserves all labels and callbacks. Production styling is rejected
for now; custom emoji eligibility is unverified and no icons are enabled.
The report contains a locally checked serialization comparison and a client
test procedure. Real before/after screenshots and accessibility/fallback
rendering checks remain blocked by unavailable Telegram client access.
Keep this task OPEN until that evidence exists.

