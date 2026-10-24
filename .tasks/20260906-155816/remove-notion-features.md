# Remove Notion-backed bot features

- STATUS: OPEN
- PRIORITY: 1

## Problem

The `/add_tasks`, `/trash`, and `/get_trash` flows depend on Notion and should be removed rather than repaired. After both flows are removed, the Notion service, token configuration, and runtime dependency become unused.

## Plan

1. Remove the task and Braintrash handler modules from router setup.
2. Remove their commands from command registries and default command descriptions.
3. Delete the unused Notion service and its configuration variables.
4. Remove `notion-client` from project dependencies and regenerate lock and requirements files.
5. Remove tests and documentation that only describe the deleted features.
6. Verify that no Notion imports, tokens, database IDs, or commands remain.

## Acceptance criteria

- The bot no longer registers `/add_tasks`, `/trash`, or `/get_trash`.
- No project-owned Python code imports `notion_client` or the old Notion service.
- Notion configuration and dependency entries are gone.
- The full test suite and static checks pass.

## Implementation and validation, 2026-10-24

The handlers, router registrations, command registry entries, service, token
configuration, environment template entry, dependency, and README references have
been removed. The default command descriptions already omitted these commands.
The lockfile and both requirements files have been regenerated.

- Full tests: 106 passed, 13 skipped, compared with 105 passed, 13 skipped before
  this change. One regression test checks that the `/list` response omits the
  retired commands, without the removed dependency installed.
- `make lint FILE='bot/configs/commands.py bot/configs/env.py bot/handlers/user/__init__.py bot/tests/handlers/test_retired_commands.py'`
  passes Ruff, typos, mypy, and pyright.
- `uv lock --check` and `git diff --check` pass.
- Full `make lint` still stops at existing Ruff findings: 379 after this change,
  compared with 391 on the unchanged starting commit. Unrelated lint cleanup is
  outside this task's scope.

This task remains open because its full static-check acceptance criterion is not
yet met. The feature removal is implemented and can be used by the command
registry follow-up.

