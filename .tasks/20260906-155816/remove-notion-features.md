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

## Implementation and validation, 2026-10-25

The handlers, router registrations, command registry entries, service, token
configuration, environment template entry, dependency, and README references have
been removed. The default command descriptions already omitted these commands.
The lockfile and both requirements files have been regenerated.

The branch now includes a normal merge of `dev-3.0` at
`2db43ed99af695c841ed7c29194df88da8d42225`. Import ordering from PR #32 and the
base branch's dependency upgrades and test/documentation removals are preserved.

- Full tests: 162 passed, 13 skipped. The retained regression checks that the
  `/list` response omits the retired commands, without the removed dependency
  installed. The three implementation-coupled cases remain deleted.
- Ruff, typos, and pyright pass for the changed Python files. Focused `make lint`
  stops at an existing mypy error in `bot/handlers/prompt/generate_image.py:43`:
  its media list does not include `InputMediaLivePhoto`. The same error reproduces
  on the selected dev snapshot; this file has no diff against that snapshot.
- `uv lock --check` and `git diff --check` pass.
- Full `make lint` stops at 196 Ruff findings, compared with 206 on the selected
  dev snapshot. Comparing filename, rule, and message finds no introduced
  findings. Unrelated lint cleanup is outside this task's scope.

This task remains open because its full static-check acceptance criterion is not
yet met. The feature removal is implemented and can be used by the command
registry follow-up.
