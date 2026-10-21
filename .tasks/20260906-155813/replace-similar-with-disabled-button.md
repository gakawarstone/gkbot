# Replace Similar callback with a disabled button

- STATUS: OPEN
- PRIORITY: 1

## Problem

The feed keyboard advertises a Similar action, but its callback branch is a stub and does not select items from the requested feed. Telegram Bot API 10.3 supports native disabled inline buttons, while the project pins `aiogram==3.26.0`, which does not expose that field.

## Plan

1. Complete the aiogram 3.31 upgrade task with typed Bot API 10.3 support.
2. Render Similar as `InlineKeyboardButton(disabled=DisabledButton())`.
3. Replace other display-only callbacks such as carousel page indicators with disabled buttons.
4. Remove obsolete callback values, branches, and commented implementations that only support those placeholders.
5. Update keyboard and callback tests.

## Acceptance criteria

- Similar remains visible but cannot send a callback.
- No `show_all_feed` callback branch remains.
- Dependency and lock files agree on the aiogram version.
- The full unit test suite and static checks pass.
