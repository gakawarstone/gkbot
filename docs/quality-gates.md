# Quality gates

Run `uv sync --frozen --dev --python 3.13` once, then `make check`. The check
runs Python lint/type checking, offline Python tests, and Serveo's Go tests and
vet. `make lint FILE=bot/path/to/file.py` and `make test FILE=bot/tests/path`
remain available for focused work. `make check-go` runs just the Go checks.
Go 1.23.1 or newer and a C compiler are needed for the Go race detector.

Ruff 0.17.2 and typos 1.51.1 are development dependencies in `uv.lock`.
Make targets use `uv run`, and pre-commit pins the same Ruff version. Updating
them is an explicit dependency change rather than a different check on each
fresh machine. Comments in `pyproject.toml` explain the import configuration.

The `Quality` workflow runs on pull requests and pushes to `dev-3.0`. The
existing deployment workflow calls the same workflow and waits for both its
Python and Serveo jobs before deployment. The quality workflow itself needs
no deployment secrets or provider credentials.

## Type checking imports

Runtime and pytest resolve imports from `bot/`. Mypy now uses the same source
root through `mypy_path` and `explicit_package_bases`. Missing internal imports
and missing typed dependencies remain errors. There is no global
`ignore_missing_imports` setting.

The only package overrides are `gallery_dl`, `gtts`, `varname`, `youtube_search`,
and `wikipedia`, including their applicable submodules. The installed releases
have neither usable bundled stubs nor a `py.typed` marker. These imports remain
`Any` until typing support is added. `types-requests` and `types-yt-dlp` provide
stubs for requests and yt-dlp instead of suppressing their imports. Recheck the
exemption list when updating these dependencies.

This follows mypy's [per-package missing-import guidance](https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports).
The image handler uses aiogram's installed `MediaUnion`, matching
[`Message.answer_media_group`](https://docs.aiogram.dev/en/latest/api/types/message.html#aiogram.types.message.Message.answer_media_group),
including the live-photo variant added to that union. Message doubles use
`MagicMock(spec=Message, ...)` rather than assigning `__class__`.

Shared caches and static option dictionaries have explicit `ClassVar`
annotations. A scheduled callback can raise any application exception, so its
retry boundary retains a local `BLE001` exception with a comment. Other
previously broad handlers catch the relevant errors or propagate failures.
Invalid Notion deadlines return a validation message; storage failures propagate
instead of appearing to be invalid user dates.

## Offline and external tests

`make test` sets `INTEGRATION_TEST=0`. Handler doubles record awaited calls and
return editable/deletable message doubles. The retained regressions check album
bytes, storage-error propagation, file contents and cleanup without making
provider requests.

Use `make test FILE=-rs` to print skip reasons. Each external test identifies
its dependency and requires `INTEGRATION_TEST=1` to opt in:

- Telegram handler checks need Bot API credentials and `ADMIN_IDS`, plus their
  named TikTok, Instagram, X, VK, article, or YouTube endpoint. Video downloads
  also need the specified yt-dlp/ffmpeg tools or yt-dlp worker.
- OpenRouter checks need network access and an API key.
- Speech integration checks need Microsoft Edge TTS or Google Translate TTS
  network access.

These checks do not run in the offline CI suite. `make debug FILE=...` remains
an explicit interactive integration command; ordinary test helpers have no
embedded debugger calls.

## Serveo lifecycle

Serveo now has a standard Go module and tests without external services. Tests
use temporary files and a helper subprocess instead of contacting serveo.net or
relying on an installed SSH executable.

SIGINT or SIGTERM cancels the service context. Shutdown stops and waits for the
SSH process, removes the advertised URL file, and calls
[`http.Server.Shutdown`](https://pkg.go.dev/net/http#Server.Shutdown) with a
five-second timeout, then closes the listener if graceful shutdown times out.
Tunnel startup failures, missing URLs, URL-file write failures, and early SSH
exit also clean up the HTTP server and child process. The SSH output is drained
before waiting for the child, avoiding a full output pipe.

The service still serves `/files` on port 8089 and forwards through serveo.net.
It now exits with an error when startup fails or the tunnel stops, rather than
remaining alive with an unusable tunnel. URL extraction, startup cancellation,
tunnel exit, and process/URL cleanup are covered by `go test -race`; `go vet`
checks the reachable shutdown flow.

## Verification after test review

`make check` passes with 132 Python tests passed and 13 external tests skipped;
Ruff, typos, mypy, Pyright, Go race tests, and vet all pass. Mypy checks 418 source
files. Go race tests and vet also pass with `GOTOOLCHAIN=go1.23.1`, the version
selected by CI. `actionlint` 1.7.7 accepts both workflows. A missing-dependency
probe still fails with mypy's `import-not-found` error.

The Python suite reports five existing dependency warnings about Tortoise's
`pk` argument and varname's optional `pure_eval` package. They do not fail the
gates. No live provider, Telegram, or serveo.net check was performed.
