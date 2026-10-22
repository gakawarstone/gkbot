# Comment debt audit, 2026-10-22

The starting commit is `dfdecceb2e97824e924538bf7720c2547a7156a7`. A scan of `bot/` found 18 TODO/FIXME markers. This change resolves six, leaving 12 in this branch. The table accounts for every starting marker. Remaining markers stay in this branch until their follow-up changes are integrated.

The referenced `review.md` is absent from this checkout and tracked files. There is no `ask.py` to deprecate or restore. TTS already has providers in `bot/services/tts/providers.py`, a service, and provider tests; the task's example of a missing TTS provider does not describe the current code.

## Resolved

| Location | Result and verification |
| --- | --- |
| `bot/core/types.py` | Replace the local chat enum with `aiogram.enums.ChatType` at its call sites. |
| `bot/filters/chat_type.py` | Normalize one or several allowed types once. Compare the incoming type directly so channel and sender events return false when excluded. Test all installed enum values with single, multiple, and empty allowed types. |
| `bot/core/keyboard_builder.py` | Construct `ReplyKeyboardMarkup` directly from the existing rows and options instead of creating a builder only to export it. |
| `bot/extensions/handlers/callback/carousel.py` | Preserve the string item ID when rebuilding markup. Declare that contract on the base markup. Tests navigate with `opaque-id` and `0012`, checking that neither fails or changes. The callback migration thread has agreed to preserve this contract. |
| `bot/services/converters/tests/parsers/platonus.py` | The final buffer was already appended. Remove the stale warning and test one and two questions with no final newline, a final newline, and a blank final line. |
| `bot/services/timezone.py` | Use `update_or_create` with the user ID as lookup and the offset in `defaults`. Treat only `None` as missing, so UTC is valid. A real in-memory SQLite test creates and updates UTC repeatedly, checks nonzero offsets, and verifies another user's value stays unchanged. |

The enum and upsert APIs were checked against the installed aiogram 3.26.0 and Tortoise ORM 0.21.6 symbols and implementation. Their official references are [aiogram enums](https://docs.aiogram.dev/en/v3.26.0/api/enums/) and [Tortoise models](https://tortoise.github.io/models.html). No dependency upgrade is needed. The separate aiogram 3.31 upgrade thread does not change the enum call sites.

## Follow-up work

| Location and marker count | Disposition |
| --- | --- |
| `bot/handlers/user/books/messages/add/create.py`, `bot/handlers/user/books/messages/edit_property/get_new_value.py`, `bot/services/repositories/books.py`: 3 | [Book persistence and validated edits](../.tasks/20261022-todo-followups/books-handler-boundaries.md). Define editable fields, parse values, and enforce the acting user's ownership before changing the handler flow. |
| `bot/handlers/user/road/habits/__init__.py`: 1 | [Habit persistence and input validation](../.tasks/20261022-todo-followups/habits-persistence.md). Extract persistence together with retry behavior for malformed input. |
| `bot/handlers/user/road/pomodoro/restart.py`: 1 | [Restart confirmation extraction](../.tasks/20261022-todo-followups/pomodoro-restart-extension.md). The current helper captures a handler and depends on road FSM and cleanup keys; moving the file is insufficient. |
| `bot/handlers/user/platonus2indigo/convert_file.py`: 1 | [Export batch size](../.tasks/20261022-todo-followups/platonus-export-batch-size.md). Preserve 25 as the current default; do not invent an external format restriction or a settings flow. |
| `bot/tests/handlers/test_feed.py`, `bot/tests/handlers/test_pomodoro.py`: 3 | [Explicit handler test fixtures](../.tasks/20261022-todo-followups/handler-test-fixtures.md). Parameterize URLs and setting values and remove assumptions about button row layout. |
| `bot/services/tiktok/extractor/_base.py`: 2 | Implemented separately in [PR #17](https://github.com/gakawarstone/gkbot/pull/17), commit `40d9f9c1f4a8fdbe67b1ecec84c31ab80abbbc26`, open and awaiting merge as of 2026-10-22. It removes both markers, preserves `get_video_file_url` as a shared compatibility entry point, and limits redirect normalization to replacing `/photo/` with `/video/` while preserving the domain and creator and removing query and fragment. The implementation thread reports shared contract coverage for all eight provider entries. These changes are not included in this branch's marker count. |
| `bot/modules/feed/handlers/_item_processor.py`: 1 | Already covered by [the processor registry](../.tasks/code-smell-cleanup/10-add-feed-processor-registry.md) and [filter relocation](../.tasks/code-smell-cleanup/13-remove-feed-processor-inheritance.md). Keep prefix routing until those migrations replace it. |

## Reproduce the scan

Run `rg -n 'TODO|FIXME' bot` from the worktree. Count matching lines with `rg -n 'TODO|FIXME' bot | wc -l`. Exclude `.tasks` and this report when comparing code counts.

The clean starting worktree passed `make test` with 105 passed and 13 skipped. Its `make lint` stopped at 391 Ruff findings, before the other lint stages. These existing findings are outside this change's scope.

After the changes, `make test` passes with 129 passed and 13 skipped. The focused parser, timezone, carousel, and filter run passes all 26 cases. `make lint FILE=...` passes Ruff, typos, mypy, and Pyright for all 13 changed Python files. `git diff --check` also passes.
