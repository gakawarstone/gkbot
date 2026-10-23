# Shared HTTP service

`services.http.HttpService` keeps one lazy aiohttp session per application run.
The existing classmethod API is unchanged. `BotStarter` closes the session after
polling, startup failure, or cancellation. Standalone scripts and tests should
call `await HttpService.close()` in their own `finally` block. Close is idempotent;
a later request can create a new session inside its running event loop.

## Timeouts and body limits

aiohttp requests use explicit deadlines:

- Total request: 120 seconds.
- Connection, including waiting for a pooled connection: 10 seconds.
- Socket connection: 10 seconds.
- Socket read: 30 seconds between received chunks.

`get`, `post`, and `get_with_downloader` return at most 50 MiB. `get_json` and
`post_json` accept at most 8 MiB before JSON decoding. Limits count actual body
bytes, including decompressed aiohttp responses and responses without a declared
length. A declared uncompressed length above the limit is rejected immediately.
The downloader reads at most the limit plus one byte from disk. File downloads
do not load their contents into memory and have no in-memory body limit.

`get_redirected_url` and `extract_cookies` check status and return response
metadata without loading the body. aiohttp follows redirects with its default
limit of ten. All methods reject final 4xx and 5xx statuses before reading or
decoding the body. JSON methods require `application/json` or an `application/`
media type ending in `+json`.

The session uses a `DummyCookieJar`: cookies are exposed by `extract_cookies`,
but are not stored or automatically replayed across requests or redirects.
Callers that need cookies must supply a `Cookie` header.

The timeout and limit settings are class attributes on `HttpService`. Change
them before creating the application session; tests use short finite deadlines.

## Failure contract

Catch `HttpRequestError` for aiohttp transport, HTTP status, timeout, invalid URL,
JSON decoding, Unicode/charset decoding, decoder recursion, and body-size errors.
The underlying exception is retained as `error.__cause__`. Oversized bodies use
`ResponseTooLargeError` as their cause. Request serialization and other caller
programming errors are not translated.

Downloader process failures retain `CalledProcessError`, `TimeoutExpired`, or
`OSError` as the cause. Response-file reading errors are translated too. Cache
directory allocation and cleanup errors remain visible as filesystem errors.
Consumer exceptions raised inside a downloaded-file context propagate unchanged.

Cancellation propagates as `CancelledError`. Downloader and disk-reader workers
finish before their cache directory is deleted, even after repeated cancellation.
This can delay cancellation until the downloader deadline expires.

## Download ownership

`download_file` retains the temporary-media ownership contract:

```python
async with HttpService.download_file(url) as file_path:
    await upload(file_path)
```

The path is valid only inside the context. Cleanup runs after upload success,
failure, and cancellation. `download_file_to_path(url, output_path)` writes to a
caller-owned path and does not delete the path or its parent on failure.

Both file downloads and `get_with_downloader` retain aria2 as their transport.
It runs without user configuration, with a 10-second connection timeout,
30-second read timeout, one attempt, and a 120-second process timeout.
`subprocess.run` kills and reaps the process on timeout. Nonzero exit status is
an error. `get_with_downloader` always cleans its own cache directory.

The separate gkfeed HTTP implementation and its bounded process decoder are
unchanged by this service.

## Checks

```sh
make test FILE=bot/tests/services/test_http.py
make lint FILE="bot/services/http.py bot/core/bot.py bot/tests/services/test_http.py"
make test
```

Tests use a local aiohttp server for all six aiohttp methods, with successful
requests, redirects, error statuses, connection failures, deadlines, invalid
JSON/encoding, truncated bodies, chunked and compressed size limits, session
reuse, cancellation, and bot lifecycle cleanup. Downloader tests cover all
three public entry points, process failures, ownership, and repeated cancellation.
Tests using the real aria2 executable skip when it is not installed.

API references: [aiohttp 3.13.3 client reference](https://docs.aiohttp.org/en/v3.13.3/client_reference.html),
[aria2 manual](https://aria2.github.io/manual/en/html/aria2c.html), and
[Python subprocess timeout behavior](https://docs.python.org/3.13/library/subprocess.html#subprocess.run).
