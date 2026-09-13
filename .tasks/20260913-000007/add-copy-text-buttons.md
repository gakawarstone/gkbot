# Add copy-text buttons where users copy values

- STATUS: OPEN
- PRIORITY: 4

## Problem

Some flows send URLs or identifiers that users may need to select and copy manually. Telegram supports `CopyTextButton`, but adding it everywhere would clutter keyboards.

## Plan

1. Identify outputs that users actually copy, such as generated links, feed URLs, or identifiers.
2. Add copy buttons only to those messages.
3. Keep navigation and action buttons in a predictable order.
4. Add keyboard tests for button text and copied value.

## Acceptance criteria

- Each added button copies the exact visible or documented value.
- No copy button duplicates an existing open-link action without a clear use case.
- Callback routing is unchanged because copy buttons do not emit callbacks.
- Keyboard tests pass.

