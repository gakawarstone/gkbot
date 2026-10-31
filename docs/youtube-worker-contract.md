# YouTube worker contract decision

Status: proposed, awaiting an explicit owner decision. Audited on 2026-10-23
against GKBot `dfdecceb2e97824e924538bf7720c2547a7156a7`.

## Recommendation and decision gate

Choose **A: retain the external gkbroker protocol**. The current client and a
running local worker already use it. Harden the client through the shared-payload
and bounded-polling tasks. Keep broker/worker deployment outside root Compose.

Owner selection: **pending**. Record the selected option, owner, date, and accepted
schema/failure policy here before runtime or deployment changes. The owner must
also confirm production GKBot's broker and worker revision without sharing
credentials. The local observations below do not establish that pairing.

## Verified contract map

### Caller, environment and deployment

- [YtdlpDownloader](../bot/services/ytdlp/downloader.py) sends URLs matching
  `^https://(?:www\.)?youtu` to the worker; other sources use local yt-dlp.
  [workers/yt_dlp.py](../bot/workers/yt_dlp.py) sends `POST /enqueue` with
  `{"function":"ytdlp.extract_info","data":["<video-url>"]}` or
  `{"function":"ytdlp.download_video","data":["<video-url>",{}]}`.
  It polls `GET /result/<task_id>` until `completed`, then fetches the result
  again. There is no overall deadline or terminal-failure handling.
- Metadata is a JSON string decoded to a dict with `title` and optional
  duration/dimensions. Downloads return a URL consumed by `URLInputFile`; audio
  also downloads that URL locally for ffmpeg preparation.
- [configs/env.py](../bot/configs/env.py) loads optional `BROKER_URL` at import
  time through python-dotenv. Missing configuration raises `ValueError` at the
  worker call. There is no broker auth configuration. `YOUTUBE_API_KEY` belongs
  to the separate YouTube API integration.
- [HttpService](../bot/services/http.py) has no worker deadline or HTTP status
  check. It translates only some request errors into `HttpRequestError`;
  transport, timeout, JSON and schema failures have no common worker contract.
- [Root Compose](../docker-compose.yml) starts only `gkbot` with bridge networking.
  It loads `BROKER_URL` through `.env`, but provides no broker/worker service or
  dependency. [.env.dist](../.env.dist) and [README](../README.md) omit the setting.
  [Deploy](../.github/workflows/deploy.yml) runs `make docker-update` over SSH on
  `master`; it does not identify the deployed broker or worker revision.
- [Commit 02c5be1](https://github.com/gakawarstone/gkbot/commit/02c5be136aeaa5d735a3c0d9380b3d397eb113c4)
  deleted `services/ytdlp_workers_supervisor`. Its `GET /fetch` read URL/ID pairs
  from `/files/tasks`; `POST /upload` accepted multipart `id` and `video`.
  It had no enqueue, result-state or function-dispatch contract. The remaining
  `services/bot-api` and `services/serveo_file_server` provide Telegram's API and
  tunneled file serving, respectively, not task brokering.

### Broker and running worker

Broker source was checked at
[`1cd7dbde74c888053e32abebbaea08615585474a`](https://github.com/gakawarstone/gkbroker/tree/1cd7dbde74c888053e32abebbaea08615585474a).
The contracts come from
[api.py](https://github.com/gakawarstone/gkbroker/blob/1cd7dbde74c888053e32abebbaea08615585474a/app/api.py),
[models.py](https://github.com/gakawarstone/gkbroker/blob/1cd7dbde74c888053e32abebbaea08615585474a/app/models.py),
[broker.py](https://github.com/gakawarstone/gkbroker/blob/1cd7dbde74c888053e32abebbaea08615585474a/app/broker.py),
and [tasks.py](https://github.com/gakawarstone/gkbroker/blob/1cd7dbde74c888053e32abebbaea08615585474a/app/tasks.py).

- `POST /enqueue` accepts `function: str`, `data: list`, returning
  `task_id: str`, `status: "pending"`.
- `GET /get_task?function=<name>` claims a task and changes it to `processing`.
  No available task returns null fields.
- `POST /submit_result` accepts `task_id: str`, `result: str`, setting `completed`.
  `POST /submit_error` accepts `task_id: str`, `error_message: str`, setting
  `failed` and storing that message in `result`.
- `GET /result/<task_id>` returns `task_id`, `status`, `result`. Stored statuses
  are exactly `pending`, `processing`, `completed`, `failed`; result is nullable
  string. Missing tasks return HTTP 404, `{"detail":"Task not found"}`.
- `DELETE /cancel/<task_id>` deletes a pending task and returns `cancelled`.
  Later GET returns 404; `cancelled` is not a stored/result status. Processing
  tasks cannot be cancelled through this API.
- Storage is in memory; restart loses tasks. There is no worker lease/requeue.
  Completed/failed tasks expire one day after creation, checked hourly.
  Pending/processing tasks do not expire.

Read-only inspection found running container `gkworker-ytdlp-app-1`, whose
`/app/main.py` SHA-256 was
`54bc1fb0e03c118d2d7d76f30b97b4ab42220a6c5db19b174ba874aa2a5c43c1`.
It claims both `ytdlp.*` functions using a hard-coded broker address and submits
JSON metadata or a presigned download URL, valid for 3600 seconds.

**Worker errors also go through `/submit_result`.** Extraction/download exceptions
produce the result string `{"status":"failed","error":"<message>"}`. The outer
task is then `completed` despite operation failure. This worker does not call
`/submit_error`; failed submission can leave a task in `processing`.

Read-only probes of its broker returned OpenAPI HTTP 200 with these six routes
and matching input schemas, and HTTP 404 for a fresh unused task ID. OpenAPI has
no result response schema; stored statuses are source-verified, not observed live
transitions. The deployed broker commit is unknown. No tasks were changed.

No GKBot container was running locally, and the audit shell had no `BROKER_URL`.
The root checkout and its `.env` were not accessed. Production pairing remains
unverified; endpoint addresses, credentials, signed URLs and logs are omitted.

## Bounded alternatives

### A. Retain the external broker, recommended

Low migration cost: client validation, shared payload retrieval, bounded polling,
handler cleanup and configuration docs. No broker API or worker migration is
required. Existing embedded failures must remain supported even if a later worker
starts using `/submit_error`.

Outages, broker restart, stuck tasks and URL expiry remain possible. The client
policy below bounds waiting, but cannot stop worker work after its deadline.
Validate with stubbed transport and a disposable broker using the cases below.

### B. Add a compatible local broker

Medium cost: pin/package the broker, configure Compose networking, health checks
and a reachable worker. A broker alone cannot download videos. Keep A's schema;
local deployment alone does not add persistence or leases. Queue reset invalidates
existing task IDs. In addition to A's tests, smoke-test worker connectivity,
download/file access, worker death and broker restart in disposable Compose.

### C. Design a supervisor replacement

High cost: the deleted code only transferred files and read a task-list file.
A replacement needs task creation, functions/options, metadata, failure state,
cancellation, concurrency and file publication/retention. Partial uploads, stale
task files and restarts need recovery rules. Test concurrent claims, interrupted
uploads, isolation, restart recovery and both result types. Choosing C requires
another reviewed protocol design before implementation.

## Proposed contract for A or compatible B, not yet approved

### Payload validation and results

- Enqueue must return an object with a nonempty string `task_id` and
  `status: "pending"`. Validate it before constructing a result URL.
- One shared helper retrieves and validates one result object per poll. Required
  fields are `task_id`, `status`, `result`. `task_id` must equal the requested ID;
  `status` must be one of the four source-verified statuses; `result` must be a
  string or null. Extra fields may be ignored for forward compatibility.
- `pending` and `processing` keep waiting. Their null or empty result is valid.
  `completed` requires a nonempty string. `failed` ends immediately, even if its
  result is null or empty, using a generic failure message when necessary.
- Completed `null`, `""`, `false`, `0`, arrays and objects are protocol errors.
  Strings such as `"0"`, `"false"` or `"{}"` pass string validation, then fail
  operation-specific validation. Never use truthiness as a substitute for type
  validation. Whitespace-only results fail operation-specific validation too.
- A completed result containing a JSON object with `status: "failed"` is a
  legacy worker failure for either operation. It must raise a task failure before
  trying to use it as metadata or a download URL. Do not depend on the presence or
  type of the optional embedded `error` field to classify the failure.
- Metadata success must decode to an object with a nonempty string `title`, as
  required by the current caller. Download success must be an absolute HTTP/HTTPS
  URL with a host. Invalid JSON, metadata or download URLs are protocol errors.
- Consume the completed payload directly. Do not GET it again for the result.

### Failure and exception policy

The shared helper and polling work must use one common exception hierarchy. These
are proposed names, not symbols that exist in the audited code:

- `WorkerError` is the common base handled at the download UI boundary.
- `WorkerConfigurationError` covers missing broker configuration and invalid
  timeout/interval settings.
- `WorkerUnavailableError` covers transport errors and every non-2xx HTTP
  response, including 404. A missing task may be cancelled, lost or expired; do
  not claim which cause occurred without evidence. Fail immediately.
- `WorkerProtocolError` covers non-object/malformed JSON, missing fields, wrong
  types, mismatched IDs, unsupported statuses and invalid completed results.
  Unknown statuses, including a result status of `cancelled`, terminate with this
  exception. They must never keep polling.
- `WorkerTaskFailedError` covers outer `failed` and legacy embedded failures.
  Preserve task ID, operation and status as structured diagnostic context.
- `WorkerTimeoutError` covers expiration of the overall operation deadline,
  including enqueue, result requests and sleeps.
- Propagate `asyncio.CancelledError`; it represents local caller cancellation.
  Do not turn it into a worker failure or call broker cancellation automatically.

Check HTTP status before parsing JSON. Do not retry or automatically re-enqueue
on failure. A failed enqueue response may follow a successfully created task.
Proposed settings are `YTDLP_WORKER_TIMEOUT_SECONDS=300` and
`YTDLP_WORKER_POLL_INTERVAL_SECONDS=1`, both finite and greater than zero. Use a
monotonic overall deadline and cap requests/sleeps by remaining time. A separate
metadata call and download call each receive their own deadline.

Handlers must clean up status messages on failure/cancellation and show a short
download error. Logs may include operation, task ID, last status and exception
category. Do not dump broker response bodies, raw worker error messages, endpoint
credentials or signed download URLs into logs or user messages.

### Implementation ownership and validation after approval

- Shared payload task #19 owns common payload retrieval/validation and common
  exceptions. It leaves polling deadlines and UI behavior to the polling task.
- Bounded polling owns the finite wait, operation-result decoding/validation,
  legacy embedded failure detection and handler cleanup. It consumes the helper's
  completed payload without refetching it. Configuration errors and HTTP failures
  must use the same hierarchy across both tasks.
- Unit tests must cover every stored status; missing, failed, unknown and
  malformed tasks; wrong/missing completed results and falsey values; invalid
  metadata/URL results; embedded failures for both operations; HTTP/transport
  errors; no repeated GET on completion; hung requests; deadlines; and propagated
  local cancellation. Integration tests must use an isolated broker, not live
  production enqueue/claim routes.
