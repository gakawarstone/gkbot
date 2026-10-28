Title: Keep the complete local YoutubeDL lifecycle off the event loop

Base: `dev-3.0`

TikTok's first extractor constructed and closed YoutubeDL on the event loop while only extract/download ran in the executor. Real offline constructor controls delayed a ready feed delete callback by 17–20 ms on warm calls. Move construction, context entry, extraction/download, context exit and output-path checks into one executor job. Keep cancellation pending until the job finishes, and until the following video conversion finishes, so directory cleanup cannot race a writer.

The controlled TikTok view flow now reaches delete with 5.37 ms median lateness instead of 18.53 ms across 10 warm repetitions. The remaining roughly 5 ms is GIL/scheduling contention. This does not claim to identify a specific production freeze or solve polling-slot exhaustion. Source HTTP, conversion, scheduler and Telegram I/O are stubbed; YoutubeDL construction and context lifecycle are real. Timers are armed before the measured operation, and both final fresh-process series use the shared measurement flock.

Validation:

- Full `make test` in this worktree, run by the parent under the shared measurement flock with the shared venv: 180 passed, 13 skipped, 5 existing warnings, 4.71 s.
- The parent also tested all four independent fixes together in a temporary snapshot: 202 passed, 13 skipped, 5 existing warnings, 11.60 s. The source branches were kept separate.
- 52 targeted tests pass, including 19 new lifecycle, callback/delete, cancellation, path and worker regressions.
- Mypy and pyright pass for the production file and new tests.
- New tests/benchmark pass Ruff; typos, formatting and diff checks pass.
- Targeted `make lint` stops at an unchanged TRY004 on invalid-metadata ValueError, reproduced on the baseline.
- Reproducible harness, raw before/after records and full scope/limitations are in `benchmarks/feed_loop/tiktok/`.

Gallery-dl has its own independent track. Snaptik, callbacks.py, the shared HTML parser and FeedDecoder are outside this change.

Snaptik's synchronous decoder was measured on generated valid responses. Large synthetic inputs delay delete, but production response sizes and fallback frequency remain unverified. This PR leaves that investigation open rather than treating it as a confirmed or resolved production cause.
