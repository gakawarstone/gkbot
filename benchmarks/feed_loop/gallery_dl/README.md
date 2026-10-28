# gallery-dl DataJob lifecycle and feed deletion readiness

The cold `DataJob(url, file=None)` constructor blocks the event loop at
`dev-3.0` revision `2db43ed99af695c841ed7c29194df88da8d42225`. Only `job.run`
previously ran in the executor. The constructor selects the URL extractor and
lazily imports extractor modules and compiles their patterns before reaching
TikTok. This delays an unrelated feed callback and its message deletion.

The fix moves construction, execution, status/exception validation and result
access into one `asyncio.to_thread` operation. The slideshow serializer keeps
its existing behavior. This change targets deletion readiness while another
post is being processed. It does not aim to shorten the next post's processing.

## Reachability and behavior

The actual `_EXTRACTORS` chain starts with `YtDlp`, `ApiExtractor`, then
`GalleryDl`. A controlled probe makes the first two sources raise
`SourceInfoExtractFailed` and stubs the redirect HTTP boundary. It then runs
the real fallback, `DataJob`, TikTok extractor, JSON parsing, dispatch and
slideshow serialization. The generated HTML fixture produces two image URLs,
an audio URL and 720 by 1080 dimensions. No source probability or live TikTok
success rate is inferred from this experiment.

The seven regression cases use real `DataJob` execution. They cover the
fallback order, thread ownership through result access, successful metadata,
nonzero status, recorded dispatch exceptions despite a zero return status,
empty data, unsupported URLs and cancellation with success or failure.

`file=None` keeps JSON output disabled. This service returns metadata and
does not create a bot media/cache directory to delete. Cancellation uses the
existing `wait_for_completion` helper. Repeated cancellation waits for the
worker to finish before the caller can run cleanup. A held real extraction
checks this with a temporary caller-owned directory and a final write before
cleanup. The existing helper's failure precedence is preserved: a worker
failure propagates if it completes after cancellation; otherwise the caller
receives `CancelledError`. The running thread is not forcibly stopped.

## Final serialized experiment

Run date: 2026-10-28. Python 3.13.11, gallery-dl 1.32.7, aiogram 3.31.0,
uvloop 0.22.1, Python thread switch interval 5 ms.

The final series used 40 fresh Python processes. Each mode has ten cold
constructor-only samples and ten separate cold full-fallback samples. Each
mode also has 60 warm constructor samples, 60 warm full-fallback samples,
20 idle controls and 20 synthetic GIL controls. Before/after order alternates
between process pairs. All processes ran sequentially while the parent held
`flock /tmp/gkbot-feed-loop-audit-20261021/measurement.lock`.

Cold means a fresh process with no gallery-dl extractor selection performed
yet. OS filesystem and bytecode caches were not cleared. This is not the first
execution after installing packages. The earlier unlocked preliminary result
of 270.75 ms is provenance only and is not part of this comparison.

For each operation an independent callback is scheduled at start + 5 ms. The
probe enters the real `ItemEventHandler._handle_event` delete branch with
already resolved dummy credentials. `Message.delete` records local readiness
and returns, and the feed API deletion is an async stub. No Telegram send,
Telegram deletion, production feed deletion or source HTTP request occurs.
Socket `connect` and `connect_ex` are prohibited, and a fake `configs.env`
prevents loading deployment configuration or `.env`.

Callback/delete figures below are signed milliseconds relative to readiness.
uvloop's timer resolution occasionally produces offsets below zero, by less
than 0.9 ms in this series. The full raw results preserve these offsets. No
production percentiles are claimed.

- Cold constructor-only, ten samples per mode: callback median
  68.274 → 0.494 ms; delete median 68.287 → 0.502 ms; maximum delete
  76.428 → 1.179 ms. Operation wall median 73.299 → 73.974 ms.
- Cold real TikTok fallback, ten samples per mode: callback median
  66.702 → 0.649 ms; delete median 66.711 → 0.663 ms; maximum delete
  70.272 → 0.828 ms. Operation wall median 72.613 → 75.061 ms.
- Warm constructor, 60 samples per mode: delete median 0.353 → 0.388 ms,
  maximum 0.929 → 0.808 ms. Wall median 0.448 → 0.424 ms.
- Warm real fallback, 60 samples per mode: delete median 0.472 → -0.041 ms,
  maximum 0.891 → 1.088 ms. Wall median 0.630 → 0.721 ms.
- Idle, 20 samples per mode: delete median 0.099 → 0.094 ms,
  maximum 0.118 → 0.117 ms.

Constructor instrumentation recorded loop-thread construction for all
160 baseline jobs and none of the 160 fixed jobs.

The 5 ms heartbeat captures later stalls as well as the first callback.
After the fix, maximum heartbeat lateness was 2.048 ms for cold construction
and 2.210 ms for cold full fallback. Moving work to a thread leaves GIL and
scheduler contention. A separately labeled synthetic control spends 150 ms
in a Python CPU loop inside the real job's offline request boundary. In this
control, delete median is 5.438 → 5.213 ms and maximum is
5.739 → 10.265 ms. After-fix maximum heartbeat lateness reaches 10.282 ms.
This control demonstrates residual contention; it is not a captured TikTok
workload. Both versions already run `DataJob.run` in a thread.

This probe measures loop dispatch and the local deletion boundary. It does
not measure Telegram round trips, polling-slot admission, production load,
large live responses or the other independently owned fixes.

## Reproduction and evidence

From the repository root, after `uv sync --frozen`:

```bash
mkdir -p /tmp/gkbot-feed-loop-audit-20261021
mkdir -p /tmp/gallery-dl-audit
flock /tmp/gkbot-feed-loop-audit-20261021/measurement.lock \
  env PYTHONPATH=bot .venv/bin/python \
  benchmarks/feed_loop/gallery_dl/lifecycle.py \
  --processes 10 --repetitions 3 \
  --output /tmp/gallery-dl-audit/serialized-series.json
```

The harness loads the historical service with read-only `git show`; it does
not switch revisions or modify history. Each cold scenario gets its own child
process. The parent retains the lock for the entire series.

Final raw artifact in the shared workspace:
`/home/gws/.cache/gkbot-feed-loop-audit/20261028/gallery-dl/serialized-series.json`.
It contains every record, per-process versions, constructor thread flags,
fallback attempts and aggregate median/min/max. The neighboring
`serialized-series-*.json` files are individual process results.

SHA-256 of the final aggregate raw file:
`c7389e6e8b5982e5290516759be31a7af3b9a8b675690f090fd870f42843b6d6`.
SHA-256 of the measured harness:
`d6bb500b9579feca08ae8bead76d2ff61c0c665238977ddcb30d81825c51bdf9`.

Preliminary provenance, excluded from the comparison:
`/home/gws/.cache/gkbot-feed-loop-audit/20261028/tiktok/preliminary-trial-including-gallery.json`
and `preliminary-harness-including-gallery.py` in the same directory.

## Validation and scope

- `make test`: 168 passed, 13 skipped.
- New gallery-dl regression file: seven cases passed.
- `make lint FILE=bot/services/gallery_dl.py` and
  `make lint FILE=bot/tests/services/test_gallery_dl.py`: Ruff, typos, mypy
  and Pyright passed.
- Harness Ruff, typos and mypy passed. Its Pyright check passed with
  `uv run pyright --project benchmarks/feed_loop/gallery_dl`. The scoped
  config supplies the bot import path for a script outside `bot/`.
- Repository-wide `make lint` stops at 204 Ruff findings in existing code,
  including `UP045` in unchanged `bot/configs/env.py`. Log:
  `/home/gws/.cache/gkbot-feed-loop-audit/20261028/gallery-dl/full-lint.log`.

Runtime changes are confined to `bot/services/gallery_dl.py`. No changes to
yt-dlp, TikTok service files, callbacks, HTML parsing or the process worker.
The remaining files are regression coverage and this independent analysis
and reproduction harness. No commit, push, PR, merge or deployment has been
performed. The prepared PR targets `dev-3.0` after an explicit AGENTS exception.
