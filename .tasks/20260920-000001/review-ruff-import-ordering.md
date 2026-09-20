# Review Ruff import ordering across the project

- STATUS: OPEN
- PRIORITY: 3

## Problem

Ruff reports `I001` for many existing import blocks and rewrites imports when its automatic fix runs. The project does not currently explain which import-ordering rules are active, whether local packages are classified correctly, or whether the resulting order is the convention maintainers want.

## Plan

1. Identify the Ruff version, enabled rules, formatter settings, and any inherited defaults that produce `I001`.
2. Check how Ruff classifies standard-library, third-party, first-party, and relative imports in this repository.
3. Compare Ruff's proposed ordering with the project's intended style and Python import behavior, including modules that may rely on import side effects.
4. Decide whether to keep the rule, configure it differently, or disable it. Record the reason in `pyproject.toml` or project documentation.
5. If the rule is kept, apply the import-only fixes across the project in one mechanical change. Do not mix unrelated Ruff fixes into that change.
6. Run the full test suite and static checks. Review the diff for changed import groups and possible initialization-order regressions.

## Acceptance criteria

- The source of Ruff's import-ordering behavior is documented.
- Ruff classifies project modules correctly, with explicit configuration where detection is unreliable.
- The repository either passes the chosen import-ordering rule or disables it with a documented reason.
- Any project-wide rewrite contains import-only changes and has been reviewed for side effects.
- `make test` and `make lint` pass, or unrelated existing failures are recorded separately with their exact output.
