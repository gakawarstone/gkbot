# TikTok file I/O fix validation

Measured on 2026-10-22 at 06:40 UTC with Python 3.13.11 and uvloop 0.22.1.
The comparison executes the baseline service classes from commit
`28a0081f7b25ea2c33192b5596d1e22356f1fdd9` and the fixed service classes in this
worktree. No network, Telegram, production database or shared-cache writes occur.

## Change

TikTok passes a caller-owned output path to ffmpeg and returns an FSInputFile on
that same MP4. It no longer reads the entire slideshow into bytes, deletes its
first directory and writes a second MP4. Downloaded video bytes are saved in a
worker thread. Both paths retain the existing five-minute scheduled cleanup.
TikTok cleanup also runs in a worker thread.

The returned FSInputFile tracks active reads in this bot process. A scheduled
callback defers cleanup for another five minutes while a read is active, including
when the callback was restored from its pickled database representation. Closing
or cancelling the file iterator closes the underlying reader and clears that
state. The initial five-minute cache TTL still applies before an upload starts.
Preparation failures and scheduler failures remove their directory. Cancellation
waits for preparation to finish before removing the directory, so cleanup cannot
race a running write or ffmpeg command.

Existing FSInputFile values, dimensions, duration probing and the slideshow
music/silent branches retain their behavior. The ffmpeg bytes-returning slideshow
API remains available and cleans up its own directory. Voice conversion is
unchanged and covered by a regression test.

## Input and method

The input is an existing real cached MP4, rechecked read-only on October 22:
87,473,457 bytes, 83.421 MiB, SHA-256
`c9aaffd926636fe1bde3e653d13a649a036a58478ab4b03664a33157d23405c6`.
This is a media I/O measurement; no feed JSON snapshot is an input to it.

All scratch files use the worktree's ext4 filesystem, on the same device as the
input. The complete benchmark runs under the shared measurement flock. It uses
warm page cache, buffered I/O, a warmed executor and no fsync. Each scenario has
one excluded warmup followed by 20 recorded repetitions. Idle baselines have 20
repetitions before and after the series. End-of-run load averages were
1.66 / 2.20 / 1.85; CPU affinity and other host processes were not controlled.

A 1 ms heartbeat is armed before each operation, and every run includes at least
one sample after it finishes. Lag below is the maximum lag in each run, then
median/p95 across runs. P95 uses nearest rank. Idle windows are 25 ms long and
have more sampling opportunities than a short path handoff.

Video cases call real TikTokService.get_video with an in-memory HTTP response.
Slideshow cases call the same real service plus real ffmpeg slideshow methods,
with image preparation and subprocess execution replaced by no-ops. A copy of the
real MP4 is staged as completed ffmpeg output before timing. The initial ffmpeg
work directory and output creation are excluded equally from both versions; the
baseline's second directory, full read, removal and second write are timed. Fixed
path construction, preparation task, scheduling handoff and FSInputFile creation
are timed. The scheduler stub round-trips the real Task through pickle without
using a database. Cleanup cases time that restored task's real callback on a
single saved video. Setup and test-directory cleanup are outside the timer.

| Operation | Version | Wall median ms | Wall p95 ms | Max lag median ms | Max lag p95 ms |
|---|---|---:|---:|---:|---:|
| Video save | Baseline | 10.874 | 11.179 | 10.964 | 11.272 |
| Video save | Fixed | 11.300 | 11.582 | 0.148 | 0.725 |
| Slideshow handoff | Baseline | 21.766 | 22.262 | 21.870 | 22.363 |
| Slideshow handoff | Fixed | 0.107 | 0.115 | 0.185 | 0.197 |
| Scheduled cleanup | Baseline | 2.493 | 2.607 | 2.575 | 2.693 |
| Scheduled cleanup | Fixed | 2.536 | 2.592 | 0.353 | 0.485 |
| Idle 25 ms | Before | 25.334 | 25.401 | 0.065 | 1.107 |
| Idle 25 ms | After | 25.306 | 25.365 | 0.062 | 1.108 |

Moving a write to a thread reduces loop stalls here without reducing its wall
time. Removing slideshow's read/write round trip reduces both. These figures do
not include network, ffmpeg transcoding, metadata subprocesses, real scheduler
storage, Telegram upload or full feed processing. The staged output is a real
cached MP4, not newly generated slideshow output. Cold storage, host contention,
GIL behavior and timer noise can produce larger lag. This is not a sub-millisecond
latency guarantee for to_thread or the full production pipeline.

## Checks

- Targeted `make test FILE='bot/tests/services/test_tiktok_service.py bot/tests/services/test_ffmpeg.py'`: 18 passed.
- Full `make test` with a local autouse fixture redirecting every CacheDir into owned test scratch and SQLite in memory: 84 passed, 13 integration tests skipped.
- `make lint FILE='bot/services/tiktok/__init__.py bot/tests/services/test_tiktok_service.py bot/tests/services/test_ffmpeg.py'`: passed Ruff, typos, mypy and pyright.
- `make lint FILE=bot/services/ffmpeg.py`: stops at five pre-existing Ruff findings, three RUF012 class attributes and ASYNC230/SIM115 in unchanged voice conversion. Running Ruff on the pinned baseline reproduces these five plus two findings in the removed slideshow read. Direct typos, mypy, pyright and Ruff excluding those existing codes pass for ffmpeg.
- Ruff check for the benchmark and Ruff format check for all five Python files pass.

## Reproduce

From the worktree root with the project virtualenv installed:

```bash
mkdir -p /tmp/gkbot-feed-loop-audit-20261021 .venv/validation-artifacts
flock /tmp/gkbot-feed-loop-audit-20261021/measurement.lock \
  env PYTHONPATH=bot .venv/bin/python \
  benchmarks/feed_loop/tiktok_file_io/benchmark.py \
  --input /path/to/read-only/cached/video.mp4 \
  --output .venv/validation-artifacts/tiktok-results.json \
  --repetitions 20
```

Raw samples from this run remain in the ignored local
`.venv/validation-artifacts/tiktok-results.json`. Media, payloads and raw host paths
are not committed.
