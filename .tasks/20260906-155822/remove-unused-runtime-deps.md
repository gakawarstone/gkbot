# Remove unused runtime dependencies

- STATUS: OPEN
- PRIORITY: 3

## Problem

The project declares `asyncio`, `translate`, `pytube`, and `pure-eval` as direct runtime dependencies. Python provides `asyncio` in the standard library, and project-owned Python code does not import the other three packages.

## Plan

1. Confirm that runtime code, scripts, tests, and deployment files do not use the four packages.
2. Remove their direct dependency declarations.
3. Regenerate `uv.lock` and exported requirements files through project commands.
4. Run import, test, and container build checks where available.

## Acceptance criteria

- The four packages are not direct project dependencies.
- Standard-library `asyncio` imports remain unchanged.
- Lock and requirements files match `pyproject.toml`.
- The full unit test suite passes.

