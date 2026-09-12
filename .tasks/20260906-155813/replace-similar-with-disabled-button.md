# Replace Similar callback with a disabled button

- STATUS: OPEN
- PRIORITY: 1

## Problem

The feed keyboard advertises a Similar action, but its callback branch is a stub and does not select items from the requested feed. Telegram Bot API 10.3 supports native disabled inline buttons, while the project pins `aiogram==3.26.0`, which does not expose that field.

## Plan

1. Upgrade aiogram to version 3.31.0 or newer with typed Bot API 10.3 support.
2. Regenerate `uv.lock` and exported requirements files through the project tooling.
3. Render Similar as `InlineKeyboardButton(disabled=DisabledButton())`.
4. Remove the obsolete `show_all_feed` callback value, branch, and commented implementation.
5. Update keyboard and callback tests.

## Acceptance criteria

- Similar remains visible but cannot send a callback.
- No `show_all_feed` callback branch remains.
- Dependency and lock files agree on the aiogram version.
- The full unit test suite and static checks pass.

