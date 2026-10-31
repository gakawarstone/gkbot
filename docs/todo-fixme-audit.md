# Comment debt audit, 2026-10-22

The starting commit is `dfdecceb2e97824e924538bf7720c2547a7156a7`. A scan of `bot/` found 18 TODO/FIXME markers. This change resolves six, leaving 12 in this branch. The table accounts for every starting marker. Remaining markers stay in this branch until their follow-up changes are integrated.

The referenced `review.md` is absent from this checkout and tracked files. There is no `ask.py` to deprecate or restore. TTS already has providers in `bot/services/tts/providers.py`, a service, and provider tests; the task's example of a missing TTS provider does not describe the current code.

## Resolved

| Location | Result and verification |
| --- | --- |
| `bot/core/types.py` | Replace the local chat enum with `aiogram.enums.ChatType` at its call sites. |
| `bot/filters/chat_type.py` | Normalize one or several allowed types once. Compare the incoming type directly so channel and sender events return false when excluded. The regression test checks that a private-chat filter rejects a channel event without raising. |
| `bot/core/keyboard_builder.py` | Construct `ReplyKeyboardMarkup` directly from the existing rows and options instead of creating a builder only to export it. |
| `bot/extensions/handlers/callback/carousel.py` | Preserve the string item ID when rebuilding markup. Declare that contract on the base markup. Tests navigate with `opaque-id` and `0012`, checking that neither fails or changes. The callback migration thread has agreed to preserve this contract. |
| `bot/services/converters/tests/parsers/platonus.py` | The final buffer was already appended. Remove the stale warning and test that both questions and their answers survive parsing when the input ends immediately after the last variant. |
| `bot/services/timezone.py` | Use `update_or_create` with the user ID as lookup and the offset in `defaults`. Treat only `None` as missing, so UTC is valid. A real in-memory SQLite test creates and updates UTC repeatedly, checks nonzero offsets, and verifies another user's value stays unchanged. |

The changes use the existing aiogram enum and Tortoise upsert API without adding dependencies. The carousel retains its typed markup method and string ID contract; its classmethod calls do not need an abstract-class instantiation guard.

## Follow-up work

| Location and marker count | Disposition |
| --- | --- |
| `bot/handlers/user/books/messages/add/create.py`, `bot/handlers/user/books/messages/edit_property/get_new_value.py`, `bot/services/repositories/books.py`: 3 | [Book persistence and validated edits](../.tasks/20261022-todo-followups/books-handler-boundaries.md). Define editable fields, parse values, and enforce the acting user's ownership before changing the handler flow. |
| `bot/handlers/user/road/habits/__init__.py`: 1 | [Habit persistence and input validation](../.tasks/20261022-todo-followups/habits-persistence.md). Extract persistence together with retry behavior for malformed input. |
| `bot/handlers/user/road/pomodoro/restart.py`: 1 | [Restart confirmation lifecycle](../.tasks/20261022-todo-followups/pomodoro-restart-extension.md). There is one caller, so keep confirmation local to Pomodoro and verify handler lifetime and message cleanup rather than extracting a shared helper. |
| `bot/handlers/user/platonus2indigo/convert_file.py`: 1 | [Export batch size](../.tasks/20261022-todo-followups/platonus-export-batch-size.md). Preserve 25 as the current default; do not invent an external format restriction or a settings flow. |
| `bot/tests/handlers/test_feed.py`, `bot/tests/handlers/test_pomodoro.py`: 3 | [Explicit handler test fixtures](../.tasks/20261022-todo-followups/handler-test-fixtures.md). Parameterize URLs and setting values and remove assumptions about button row layout. |
| `bot/services/tiktok/extractor/_base.py`: 2 | Implemented separately in [PR #17](https://github.com/gakawarstone/gkbot/pull/17). These changes are not included in this branch's marker count. |
| `bot/modules/feed/handlers/_item_processor.py`: 1 | Already covered by [the processor registry](../.tasks/code-smell-cleanup/10-add-feed-processor-registry.md) and [filter relocation](../.tasks/code-smell-cleanup/13-remove-feed-processor-inheritance.md). Keep prefix routing until those migrations replace it. |

## Verification

Run `rg -n 'TODO|FIXME' bot` to reproduce the code inventory.

Against `dev-3.0` at `2db43ed99af695c841ed7c29194df88da8d42225`, the last full suite passed with 166 passed and 13 skipped. The seven focused regressions cover channel rejection without an exception, final-question retention, string ID preservation, UTC persistence, and user isolation. Test review removed redundant matrices and a mocked UTC case; simplification review adds no tests.

Global lint has 193 Ruff findings versus 204 on that base, with no introduced findings. The original 13-file lint scope also encounters the unchanged mypy error at `bot/handlers/prompt/generate_image.py:43` with aiogram 3.31. This was reproduced on the base. Full lint is not green.

After simplification, the seven focused regressions pass. `make lint FILE='bot/ui/keyboards/carousel.py bot/extensions/handlers/callback/carousel.py bot/tests/handlers/test_carousel.py'` passes Ruff, typos, mypy, and Pyright. `git diff --check` passes.
