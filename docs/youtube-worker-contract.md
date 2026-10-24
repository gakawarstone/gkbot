# YouTube worker contract decision

Status: proposed, awaiting an explicit owner decision. Audited on 2026-10-23
against GKBot `dfdecceb2e97824e924538bf7720c2547a7156a7`.
No runtime or deployment changes are authorized by this document yet.

## Recommendation and decision gate

Choose **A: retain the external gkbroker protocol**. The current client and a
running local worker already use it. Harden the client through the shared-payload
and bounded-polling tasks below. Keep broker and worker deployment outside root
Compose for this change. Do not restore the deleted supervisor.

Owner selection: **pending**. Record the selected option, owner, date, and any
changes to the proposed schema and failure policy here before implementation.
The owner must also confirm which broker and worker revision production GKBot
uses, without sharing endpoint credentials. A source match alone does not prove
the production deployment uses that revision.

## Verified contract map

### Caller and environment

- [YtdlpDownloader](../bot/services/ytdlp/downloader.py) sends URLs matching
  `^https://(?:www\.)?youtu` to the remote worker for metadata and downloads.
  Other sources use local yt-dlp. Source detection changes are a separate task.
- [workers/yt_dlp.py](../bot/workers/yt_dlp.py) enqueues
  `{"function":"ytdlp.extract_info","data":["<video-url>"]}` or
  `{"function":"ytdlp.download_video","data":["<video-url>",{}]}` with
  `POST /enqueue`, then reads `GET /result/<task_id>`.
- Enqueue currently requires only `response["task_id"]`. Polling reads
  `response["status"]` until exactly `completed`, then performs another GET for
  `response["result"]`. There is no overall deadline or terminal-failure handling.
- `get_info` JSON-decodes the result string. The downloader then expects a dict
  with `title`, and uses optional duration/dimensions. `download_video` expects a
  downloadable URL string and constructs `URLInputFile`. Audio also downloads the
  returned URL into local storage for ffmpeg preparation.
- [configs/env.py](../bot/configs/env.py) loads optional `BROKER_URL` at import
  time through python-dotenv. Missing configuration fails at the worker call with
  `ValueError`. No broker token/header configuration exists in this client.
  `YOUTUBE_API_KEY` belongs to the separate YouTube metadata API integration.
- [HttpService](../bot/services/http.py) creates a session per call. Its JSON
  helpers do not check HTTP status. They translate some aiohttp exceptions into
  `HttpRequestError`; other connection, timeout, JSON and schema errors can escape.
  There is no worker-specific request deadline.

### Compose and deployment

- [Root Compose](../docker-compose.yml) starts only `gkbot`, loads `.env`, and
  uses bridge networking. It provides no broker, worker, service discovery name,
  or broker dependency. `BROKER_URL` can enter through `env_file` despite not
  appearing in the explicit `environment` block.
- [.env.dist](../.env.dist) and [README](../README.md) omit `BROKER_URL`.
  Copying the template alone therefore does not configure YouTube downloads.
- [Deploy workflow](../.github/workflows/deploy.yml) runs `make docker-update`
  over SSH on `master`. The
  [2026-10-23 run](https://github.com/gakawarstone/gkbot/actions/runs/39924776988)
  succeeded at `fc194644844b5eb5041649f14c4fd46a27ca2cf8`. It does not identify
  the deployed broker address or worker revision.
- [Commit 02c5be1](https://github.com/gakawarstone/gkbot/commit/02c5be136aeaa5d735a3c0d9380b3d397eb113c4)
  deleted `services/ytdlp_workers_supervisor`. Its historical `GET /fetch` read
  URL/ID pairs from `/files/tasks`; `POST /upload` accepted multipart `id` and
  `video`. It had no `/enqueue`, result-state endpoint, or compatible function
  dispatch. It is not a current local alternative.
- `services/bot-api` is Telegram's Bot API service.
  `services/serveo_file_server` serves files through an SSH tunnel. Neither
  implements a task broker or the removed supervisor protocol.

### External broker and running worker evidence

The owner's public [gkbroker source](https://github.com/gakawarstone/gkbroker/tree/1cd7dbde74c888053e32abebbaea08615585474a)
was read at commit `1cd7dbde74c888053e32abebbaea08615585474a`.
The authoritative files are
[api.py](https://github.com/gakawarstone/gkbroker/blob/1cd7dbde74c888053e32abebbaea08615585474a/app/api.py),
[models.py](https://github.com/gakawarstone/gkbroker/blob/1cd7dbde74c888053e32abebbaea08615585474a/app/models.py),
[broker.py](https://github.com/gakawarstone/gkbroker/blob/1cd7dbde74c888053e32abebbaea08615585474a/app/broker.py),
and [tasks.py](https://github.com/gakawarstone/gkbroker/blob/1cd7dbde74c888053e32abebbaea08615585474a/app/tasks.py).
Its README omits failure and cancellation details present in the code.

- `POST /enqueue` accepts `function: str`, `data: list` and responds with
  `task_id: str`, `status: "pending"`.
- Workers claim tasks with `GET /get_task?function=<name>`. Claiming changes
  `pending` to `processing`. No available task returns null fields.
- `POST /submit_result` accepts `task_id: str`, `result: str` and sets
  `completed`. `POST /submit_error` accepts `task_id: str`,
  `error_message: str` and sets `failed`, storing that message in `result`.
- `GET /result/<task_id>` responds with `task_id`, `status`, and `result`.
  The status enum is exactly `pending`, `processing`, `completed`, `failed`.
  Result is nullable string. A missing task returns HTTP 404 with
  `{"detail":"Task not found"}`.
- `DELETE /cancel/<task_id>` deletes a pending task and responds with
  `status: "cancelled"`. Later result reads return 404. `cancelled` is not a
  stored/result status. Processing tasks cannot be cancelled through this API.
- Storage is in memory. Restart loses tasks. There is no worker lease/requeue
  mechanism after claiming a task. Completed/failed tasks expire based on creation
  time after one day, checked hourly. Pending/processing tasks do not expire.

Read-only Docker inspection found a running `gkworker-ytdlp-app-1` container.
Its `/app/main.py` SHA-256 was
`54bc1fb0e03c118d2d7d76f30b97b4ab42220a6c5db19b174ba874aa2a5c43c1`.
It claims both `ytdlp.*` functions through `/get_task`, returns JSON metadata or a
presigned download URL through `/submit_result`, and uses a hard-coded broker
address. Its download URL expires after 3600 seconds.

**Worker errors also go through `/submit_result`.** The worker catches extraction
and download exceptions and submits a string containing
`{"status":"failed","error":"<message>"}`. Thus the outer task can be
`completed` while the actual operation failed. The running worker does not call
`/submit_error`. Failed result submission can leave a task in `processing`.

Read-only probes of that worker's configured broker returned HTTP 200 for
`/openapi.json`, with the six routes above and matching enqueue/result/error input
schemas, and HTTP 404 for a fresh unused task ID. No tasks were submitted, claimed,
cancelled, or changed. OpenAPI has no response schema for the result endpoint, so
the four stored statuses are source-verified, not observed live task transitions.
The deployed broker's exact commit is not exposed by these probes.

No GKBot container was running on this Docker host, and `BROKER_URL` was unset in
the audit shell. The root checkout and its `.env` were not read or changed.
Consequently the production bot-to-broker pairing remains unverified. This is the
specific deployment fact the owner still needs to confirm. Endpoint addresses,
credentials, cookies, signed URLs, task payloads and container logs are omitted.

## Bounded alternatives

### A. Retain the external broker, recommended

Cost is limited to client validation, shared payload retrieval, bounded polling,
handler cleanup and configuration documentation after approval. No broker API or
worker migration is required. A later worker fix can use `/submit_error`, while
the client retains compatibility with existing embedded error results.

Failures remain external service outages, lost tasks on broker restart, stuck
processing tasks, and expired download URLs. The proposed client policy below
makes those failures finite and explicit. It does not provide server cancellation
or prevent worker work from continuing after the client deadline.

Test with stubbed transport and a disposable broker: all statuses, lost/removed
tasks, legacy embedded errors, invalid results, HTTP errors, hung requests and
deadline expiry. Exercise both YouTube callbacks and Shorts handler cleanup.

### B. Add a compatible local broker service

Keep the same wire schema and worker functions, but add a pinned broker artifact,
Compose networking, endpoint configuration, health checks and an explicit worker
connection path. A broker by itself does not download videos. An external worker
must reach the local broker, or a compatible worker must also be deployed.

Cost is medium and includes ownership of broker/worker packaging and operations.
The published broker uses memory, so simply adding Compose does not solve task
loss, stuck processing or durability. A queue reset during migration invalidates
existing task IDs. Persistence or leases would require separate broker changes.

Reuse A's client tests, then add disposable Compose smoke tests for worker
connectivity, a completed download, worker death, broker restart and file access
from the bot. Do not add this deployment before the owner chooses it.

### C. Build a replacement using the old supervisor approach

Cost is high. The deleted code provides file transfer and a task-list file, not a
replacement for broker state. A new design must supply task creation, function and
options transport, metadata results, failure state, cancellation, concurrency,
file publication/retention and access from the bot. There is no supported
supervisor protocol to switch to by changing an endpoint.

Partial uploads, missing metadata, stale task files and supervisor restarts would
need defined recovery behavior. Test the new state machine, concurrent claims,
upload interruption, task isolation, restart recovery and both caller result types
before cutover. Choosing C requires another reviewed protocol design before code.

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

The documentation PR can be reviewed now. Runtime work remains blocked until the
owner's selection and accepted policy are recorded here.
