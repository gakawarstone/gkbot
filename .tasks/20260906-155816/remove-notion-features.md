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

