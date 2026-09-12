# Improve pre-commit hooks with ruff

- STATUS: OPEN
- PRIORITY: 2

## Plan
1.  **Analyze**:
    -   Read `.pre-commit-config.yaml` to see current hooks.
2.  **Execute**:
    -   Add the `ruff-pre-commit` repository to the configuration.
    -   Configure `ruff` (linter) and `ruff-format` (formatter) hooks.
    -   Ensure versions match or are compatible with the project's requirements.
3.  **Verify**:
    -   Run `pre-commit run --all-files` (if pre-commit is installed) or verify the syntax of the yaml file.