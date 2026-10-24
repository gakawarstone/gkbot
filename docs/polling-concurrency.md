# Polling concurrency

`POLLING_TASKS_CONCURRENCY_LIMIT` sets the maximum number of update tasks running
at once in this bot process. It defaults to `10`. Set it in `.env` or the process
environment, then restart the bot. Docker Compose already passes `.env` through
`env_file`.

```dotenv
POLLING_TASKS_CONCURRENCY_LIMIT=10
```

The value must be a positive integer. Empty values, zero, negative numbers, and
non-integers fail at startup with the variable name in the error. Programmatic
`BotConfig` construction also rejects invalid limits, including `None` and booleans.
There is no unlimited setting.

`BotStarter` explicitly enables `handle_as_tasks=True` and passes the configured
value to aiogram's `tasks_concurrency_limit`. The
[aiogram 3.31 polling API](https://docs.aiogram.dev/en/v3.31.0/dispatcher/dispatcher.html#aiogram.dispatcher.dispatcher.Dispatcher.start_polling)
applies this limit to concurrent update processing. When all slots are occupied,
polling waits for a slot before scheduling another update. Slow handlers still
occupy a slot while awaiting I/O. This can delay commands behind long downloads
or AI streams.

## Local measurements and the default

The offline benchmark runs a burst of 40 updates through the installed aiogram
3.31.0 dispatcher and the real `/img` handler. It replaces Telegram transport,
prompt enhancement, image HTTP requests, and media upload with local stubs.
Each update enhances a prompt, fetches four separate 5 MiB image buffers in
parallel, then holds those buffers during upload. Each network stage waits
50 ms. No provider credentials or network access are needed.

Run each limit in a fresh process so peak RSS does not include earlier runs:

```bash
uv sync --all-extras
for polling_limit in 1 5 10 20; do
  PYTHONPATH=bot PYTHON_DOTENV_DISABLED=1 \
    BOT_TOKEN=12345678:ABCDEF-GHIJKLMNOPQRSTUV ADMIN_IDS=1234 \
    DB_URL=sqlite://:memory: \
    .venv/bin/python bot/benchmarks/polling.py --limit "$polling_limit"
done
```

Measured on Linux x86-64, Python 3.13.11, aiogram 3.31.0, on 2026-10-23:

| Update limit | Peak active updates | Peak simulated provider requests | Updates/s | Traced peak MiB | Process peak RSS MiB |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 4 | 6.50 | 20.41 | 271.91 |
| 5 | 5 | 20 | 31.00 | 100.49 | 351.94 |
| 10 | 10 | 40 | 58.92 | 200.60 | 448.17 |
| 20 | 20 | 80 | 97.66 | 400.82 | 647.06 |

These results support retaining `10` as a bounded starting value. It allows
parallel progress, uses about 200 MiB of traced burst allocations in this case,
and halves the buffered memory and request concurrency seen at `20`. The script
checks that every update uploads all four buffers, that active updates reach
the configured limit, and that simulated provider requests never exceed four
times that limit. Change `--response-mib`, `--updates`, or `--delay` to vary the
workload.

Throughput here reflects the stub delays, not production service capacity.
Traced memory starts after imports; RSS includes the process and imports.
The benchmark does not measure live AI streaming, media downloads, album
processing, subprocess RSS, or account-specific service limits. Larger images,
base64 copies, and longer chat histories can need more memory. The default is
not a guarantee that every workload fits a particular container size or quota.

## Tune for production

1. Measure idle process RSS and peak container memory during a representative
   burst of AI streams, downloads, albums, and `/img` requests in staging.
   Include child processes such as `ffmpeg`, disk usage, and the local Bot API
   server in the deployment's resource budget. Record handler duration, update
   arrival-to-completion latency, throughput, and provider errors.
2. Reserve memory for idle state and other work, plus operating headroom. Choose
   a limit no larger than `floor(remaining_memory / peak_memory_per_update)`.
   In the local image scenario, each active update retains roughly 20 MiB of
   image data, before other overhead. Repeat with actual response sizes.
3. Check each provider's limits for the deployed account and selected model.
   `/img` can create four image requests per active update, so `10` permits up
   to 40 concurrent image fetches and up to 10 prompt enhancements at another
   stage. An update limit does not impose a requests-per-minute limit.
   [OpenRouter documents model-dependent limits and account checks](https://openrouter.ai/docs/api_reference/limits).
   Do not infer a provider quota from the offline request counts.
4. Lower the value if memory headroom shrinks or provider throttling increases.
   Increase it in small steps only when measured memory and service capacity
   allow it and queued-update latency needs improvement. Recreate the Compose
   container after changing `.env`, or restart a directly launched process.

The limit covers polling update tasks. Child tasks inside an update, scheduled
jobs, and background work started outside polling need their own resource
budgets. Long-running child work that outlives its update is not bounded by this
setting. Provider rate limiting remains a separate concern.
