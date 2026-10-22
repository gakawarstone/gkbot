# Feed JSON decode fix

The production change moves list-response JSON decode and `FeedItem` construction
into one reusable spawned process. It retains the global fetch/cache lock. The
worker is warmed by the startup hook, after database and schedule initialization,
and also supports lazy initialization. Spawning, submission and executor shutdown
run in a thread; the JSON work runs in the process, with its own GIL.

The decoder submits at most one job. Cancelling a request leaves its running job
in that slot; a later request waits for completion before submitting another body.
The global API lock permits at most one additional downloaded body waiting for
that cancelled job. It does not create an unbounded executor queue. Completed
cancelled results and errors are discarded and observed. Shutdown rejects new
decodes, drains existing work, and joins the process off-loop. Cancelling the
shutdown caller leaves its cleanup task running. A broken pool is disposed and
the next request can create a replacement.

The request URL, credentials/cache key, five-minute TTL after completion, empty
link filtering, output fields, item order and picker/pocket behavior are preserved.
Errors propagate without caching a partial response. Hot hits do not use IPC.

## Input and method

This run used the real **22 October** snapshot, 26,394,219 bytes, captured at
2026-10-22T05:29:41Z. SHA-256:
`d39f0aaf9b8443d94c9f097c7a741382f8fca70caa05ae271aca1c3fb080b8f6`.
There are 1,000 input records and 999 output items. The snapshot includes 18
base64-bearing records. The full output was compared with baseline, including
every text field. No payload, URLs or credentials are included in these artifacts.

This is a different input from the lost 21 October 100.4 MiB snapshot. The earlier
prototype results are not measurements of this patch.

`benchmark.py` loads the actual API class at baseline revision
`28a0081f7b25ea2c33192b5596d1e22356f1fdd9` from git and compares it with the
working-tree API. Each instance has isolated cache/lock state. Only `_get_html`
is replaced, returning already-resident snapshot bytes immediately. No network,
Telegram, production database, or media operations are performed.

Python 3.13.11 with GIL enabled and uvloop 0.22.1 were used. The script holds the
shared measurement `flock` throughout the experiment. There are 20 repeats per
normal case and five fresh-process lazy first misses. Normal cases are shuffled
each repetition. Input reading, preparation, GC and cache/output disposal are
outside timing. All input/output IPC is inside the cold-call measurement.

A 1 ms heartbeat samples before and after every operation, including synchronous
baseline decode. The reported lag is the maximum heartbeat delay in each run;
p95 uses nearest rank over those maxima. The synthetic 20 ms synchronous sleep
probe gave 20.135 ms p95 lag. It only validates the sampler. `results.json`
contains timing samples and aggregate metadata, not source data.

## Observed timings

All values below are milliseconds, with median wall time followed by p95 wall
time and p95 per-run maximum loop lag.

- Current cold cache, 20 runs: **47.371 / 48.954 / 49.041**.
- Fixed cold cache with warm worker, 20 runs: **78.468 / 82.275 / 2.904**.
- Current hot cache, 20 runs: **0.086 / 0.172 / 0.231**.
- Fixed hot cache, 20 runs: **0.082 / 0.131 / 0.205**.
- Fixed lazy first miss including spawn, five runs: **230.323 / 296.261 / 9.095**.
- Idle before/after, 20 runs each: p95 max lag **0.103 / 1.107**.

The observed cold-cache lag p95 fell about 94%, while median wall time grew about
66%. The worst observed fixed warm-worker lag was 3.821 ms. These are local
observations on this input, not production latency bounds.

## Costs and limits

IPC copies the input and complete text-bearing output. The extra process and
transient decode/serialization buffers increase memory use; bounding jobs does
not bound the size of one upstream response. A cancelled running job is allowed
to finish, so it still consumes CPU and can delay the next cold request or
shutdown. There is no new hard worker timeout or forced termination policy.

Process spawning and startup imports cost time. The lazy timing above comes from
this benchmark entry point; production startup imports can differ. Normal bot
startup warms the worker before polling. A crashed-worker replacement incurs
spawn costs on the next cold miss. Serialization, unpickling and object disposal
still need the parent GIL, so larger responses can produce larger pauses. The
cache's existing total-key/payload memory policy is unchanged. No server API,
limit reduction, text truncation or new dependencies are required.

## Validation and reproduction

Regression tests cover full text/base64 preservation, empty links/feed, malformed
JSON/schema and HTTP errors, query/cache keys, TTL, cold/hot cache, same/different
key serialization, picker order/pocket, fetch/decode cancellation, bounded jobs
after repeated cancellation, worker reuse/replacement, and cleanup after cancelled
shutdown. The thread-gated cancellation tests use synthetic coordination only;
they are not performance measurements.

Checks passed: 17 targeted regression tests; full `make test` with 83 passed and
13 integration tests skipped; targeted `make lint` with Ruff, typos, mypy and
pyright all passing. Ruff formatting and `git diff --check` also passed. The
suite emitted existing Tortoise deprecation and optional `pure_eval` warnings.

Run from this checkout:

```bash
make test FILE='bot/tests/services/test_gkfeed_api.py bot/tests/services/test_gkfeed_decoder.py'
make test
make lint FILE='bot/services/gkfeed/_decoder.py bot/services/gkfeed/api.py bot/configs/startup.py bot/handlers/on_shutdown.py bot/tests/services/test_gkfeed_decoder.py bot/tests/services/test_gkfeed_api.py benchmarks/feed_loop/json_fix/benchmark.py'
PYTHONPATH="$PWD/bot" .venv/bin/python benchmarks/feed_loop/json_fix/benchmark.py \
  --input /home/gws/.cache/gkbot-feed-loop-audit/20261022/data/feed_response.json \
  --output benchmarks/feed_loop/json_fix/results_reproduced.json
```

The saved snapshot must be supplied locally. The benchmark makes no API requests.
