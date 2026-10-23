# Import ordering

Keep Ruff's `I001` rule. It groups and sorts imports consistently with the
existing convention of standard-library imports, dependencies, project modules,
then relative imports. Import ordering belongs to the linter; `ruff format`
does not sort imports.

## Configuration and tools

The audit on 2026-10-23 used `uvx ruff` 0.17.2 and also checked the import
rewrite with pre-commit's previous Ruff 0.16.7. The later quality-gates change
pins Ruff 0.17.2 in the development dependencies, lockfile, and pre-commit;
`make lint` and `make format` now use `uv run ruff`. See
[quality-gates.md](quality-gates.md) for the complete verification workflow.

Before this change, `[tool.ruff]` contained only `src = ["bot"]`. There was no
`select`, `ignore`, `extend`, formatter override, or nested Ruff configuration.
`ruff check bot/main.py --show-settings` resolved the worktree's `pyproject.toml`.
Ancestor directories contained no Ruff configuration. `--isolated` also enabled
`I001`, confirming that the rule came from Ruff's defaults rather than an
external configuration. Ruff expanded its default rule set in 0.16.0.

The project now explicitly uses `lint.extend-select = ["I001"]` to retain this
decision even if the defaults change. Other lint rules still use the installed
Ruff version's defaults. The import review did not change their selection.

Resolved settings were Python 3.13, inferred from `requires-python`, a line
length of 88, four spaces, double quotes, automatic line endings, respected
magic trailing commas, and disabled preview/docstring code formatting. Isort
settings otherwise use Ruff's defaults, including sorting names by type,
furthest-to-closest relative imports, and blank lines between sections.

To inspect the effective configuration or check imports alone:

```bash
uv run ruff --version
uv run ruff check bot/main.py --show-settings
uv run ruff check . --select I001
uvx --from ruff==0.16.7 ruff check . --select I001
```

## Module classification

Runtime execution uses `python bot/main.py`, and pytest adds `bot` to
`pythonpath`. Thus `configs`, `core`, `extensions`, `filters`, `handlers`,
`middlewares`, `models`, `modules`, `services`, `tests`, `ui`, `utils`,
`workers`, and `manage` are top-level project imports. `src = ["bot"]` lets
Ruff discover these modules without depending on the active virtual environment.
`known-first-party = ["bot"]` additionally classifies package-qualified imports
explicitly, since the `bot` package itself is outside that source root.

A stdin probe containing these packages confirmed the following groups:

- Standard library, such as `os` and `pathlib`.
- Third party, such as `aiogram` and `yt_dlp`.
- First party, including `bot` and the modules rooted at `bot/` listed above.
- Relative imports, in a separate final group.

In particular, the external top-level `yt_dlp` module stays third party while
`workers.yt_dlp` stays first party. The rewrite changes import ordering and
spacing only. It does not change absolute/relative import paths, aliases,
re-exports, or dependency versions.

## Initialization review

Python executes a module's top-level statements when first imported, so sorting
imports can change initialization order. The review covered the reordered
handler package imports, `manage.py`, middleware imports, feed modules, and
service/provider imports.

Handler and middleware registration still happens in the existing `setup()`
calls. Their call order is unchanged. `configs.env` still loads dotenv before
reading configuration, and its imports were unchanged. Startup hooks remain in
their explicit tuple; TikTok extractors and TTS providers retain their explicit
registry order. No import moved across an executable statement. Future imports
that require an ordering barrier should use a narrowly scoped `# isort: split`
or `# isort: off` / `# isort: on` with a comment explaining the dependency.

The mechanical rewrite touched 177 Python files. An AST comparison against
`fc19464` confirmed identical imported modules, symbols and aliases, and
identical non-import nodes. A fresh-process smoke check imported `manage`,
configured a dispatcher with `middlewares.setup`, `handlers.setup` and
`modules.setup`, and compared ordered router callbacks, middleware, startup
hooks, extractors and TTS providers against a `git archive` snapshot of the base.
Those results matched. The smoke check used dummy test configuration and did
not start polling or call startup hooks.

## Validation and existing failures

On base `fc19464` and after the rewrite, `make test` reported **122 passed,
13 skipped**, with five existing dependency warnings. The skipped integration
tests were not run against external services. The focused command
`make test FILE=bot/tests/handlers/test_pomodoro.py` passed all four tests.
`make lint FILE=bot/core/default_commands.py` passed Ruff, typos, mypy and pyright.

`uv run ruff check . --select I001` passes across the repository on both reviewed
Ruff versions. The full `make lint` still stops at Ruff, with **204 existing
non-import findings**, down from 383 findings including 179 `I001` reports.
Counts by file and rule are unchanged for the other rules. Three `UP035`
messages list `Awaitable` and `Callable` in the new import order.

The exact output of `RUFF_OUTPUT_FORMAT=concise make lint` is saved in
[make-lint.txt](checks/ruff-import-ordering/make-lint.txt). The environment
variable changes diagnostic rendering only. Since make stops at the first
failure, the remaining commands were also run separately:

- `uvx typos bot/` passed with no output.
- `uv run mypy bot/` reported two existing errors. See
  [mypy.txt](checks/ruff-import-ordering/mypy.txt).
- `uv run pyright bot/` reported the same two existing errors. See
  [pyright.txt](checks/ruff-import-ordering/pyright.txt).

The type errors concern the media union in
`bot/handlers/prompt/generate_image.py` and the mock `__class__` assignment in
`bot/tests/middlewares/test_downstream_results.py`. Both also reproduce in a
base snapshot with the same project configuration and virtual environment.
The exact base outputs are saved in
[mypy-baseline.txt](checks/ruff-import-ordering/mypy-baseline.txt) and
[pyright-baseline.txt](checks/ruff-import-ordering/pyright-baseline.txt).
They are outside this import review.

## Ruff references

- [Configuration discovery and defaults](https://docs.astral.sh/ruff/configuration/)
- [Ruff 0.16 default rule expansion](https://astral.sh/blog/ruff-v0.16.0)
- [I001 behavior](https://docs.astral.sh/ruff/rules/unsorted-imports/)
- [First-party detection](https://docs.astral.sh/ruff/faq/#how-does-ruff-determine-which-of-my-imports-are-first-party-third-party-etc)
- [Isort settings](https://docs.astral.sh/ruff/settings/#lint_isort)
- [Import sorting and formatter workflow](https://docs.astral.sh/ruff/formatter/#sorting-imports)
