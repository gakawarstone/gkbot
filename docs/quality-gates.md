# Quality gates

Install dependencies with `uv sync --frozen --dev --python 3.13`, then run
`make check` for Python lint/type checking, offline tests, and Serveo's Go race
tests and vet. Go 1.23.1 or newer and a C compiler are required for race tests.

Use `make lint FILE=bot/path.py`, `make test FILE=bot/tests/path`, or
`make check-go` for focused checks. Ruff and typos are locked development
dependencies; pre-commit pins the same Ruff version as the Makefile.

The `Quality` workflow runs Python and Serveo jobs on PR events and pushes to
`dev-3.0`. Deploy calls the same workflow before deployment. Existing open PRs
need a head update or reopen event after the workflow reaches their base.
PR checks do not deploy or need provider credentials.

## Missing-import exemptions

Mypy resolves the runtime source root `bot/` through `mypy_path` and
`explicit_package_bases`. Missing internal imports remain errors. Package
exemptions in `pyproject.toml` cover only `gallery_dl`, `gtts`, `varname`,
`youtube_search`, and `wikipedia`, whose installed releases lack usable bundled
stubs or a `py.typed` marker. They remain `Any`; recheck exemptions on upgrades.
Requests and yt-dlp use installed stubs instead of exemptions.

## External tests and cleanup

`make test` disables integration mode. Use `make test FILE=-rs` for the external
dependencies named in each skip reason. Live checks require
`INTEGRATION_TEST=1` and the named endpoints, credentials, or tools;
`make debug FILE=...` is the interactive integration command.

Serveo tests use local child processes without contacting serveo.net. Shutdown
and startup failures stop/reap SSH, remove the advertised URL, and close HTTP
with a bounded graceful shutdown. Python file regressions retain cleanup on
failure and cancellation; no live-provider checks are implied by offline tests.
