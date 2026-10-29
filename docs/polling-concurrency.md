# Polling concurrency

Set `POLLING_TASKS_CONCURRENCY_LIMIT=10` in `.env` or the process environment,
then restart the bot or recreate its Compose container. The default is `10`.
Values must be positive integers; invalid configuration fails at startup.
Programmatic `BotConfig` construction also rejects `None` and booleans.

The [aiogram polling limit](https://docs.aiogram.dev/en/v3.31.0/dispatcher/dispatcher.html#aiogram.dispatcher.dispatcher.Dispatcher.start_polling)
bounds concurrent update tasks in each bot process. Slow handlers occupy slots
while awaiting I/O, so a burst can delay later commands. Child tasks and
scheduled jobs require separate budgets; this setting does not limit requests
per minute or work that outlives its update.

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

The retained default `10` allows parallel progress with about 200 MiB of traced
burst allocations here, half the buffered memory measured at `20`. The script
checks completed uploads and concurrency bounds. Use `--response-mib`,
`--updates`, and `--delay` to vary the workload.

These are offline results, not production capacity. Throughput reflects stub
delays; traced memory excludes imports, while RSS includes them. Live AI
streams, downloads, albums, subprocesses, and account quotas are not measured.
Production resource acceptance remains open pending measurements or an explicit
owner decision to defer deployment calibration to rollout.

## Tune for production

- Measure idle RSS and peak container memory under representative AI, download,
  album, and image traffic. Include subprocesses and the local Bot API server.
  Record throughput, completion latency, and provider errors.
- After reserving idle memory and headroom, cap concurrency at
  `floor(remaining_memory / peak_memory_per_update)`. This image scenario holds
  about 20 MiB of buffers per update; real sizes and copies can cost more.
- Check deployed account and model quotas. `/img` fetches four images per
  update, so `10` permits 40 concurrent image fetches. Prompt enhancement can
  use up to 10 requests in another stage.
  [OpenRouter limits depend on the model and account](https://openrouter.ai/docs/api_reference/limits).
- Lower the limit on memory pressure or throttling. Increase it in small steps
  only when memory and provider capacity allow it and queued latency warrants
  it. Restart or recreate the process after changing the setting.
