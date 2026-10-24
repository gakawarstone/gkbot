# Decide the YouTube worker contract

- STATUS: OPEN
- PRIORITY: 2

## Problem

The YouTube downloader expects an external broker with `/enqueue` and `/result/<task_id>`. Root Compose does not provide that service. The former supervisor exposing `/upload` and `/fetch` was deleted in commit `02c5be1`; it is not a current local alternative. The intended deployment contract needs an explicit owner decision.

## Plan

1. Document the current caller, environment, Compose, worker, and supervisor contracts.
2. Check which service is used in the real deployment without printing secrets.
3. Propose bounded options: keep and document the external broker, add a compatible local service, or migrate to the supervisor protocol.
4. Describe migration cost, failure behavior, and test strategy for each option.
5. Stop and ask the task owner to choose an option before changing runtime code or deployment files.

## Acceptance criteria

- The task contains a verified contract map and a recommended option.
- The owner has explicitly selected the target architecture.
- Implementation starts only after that decision is recorded.

## Verified audit and recommendation, 2026-10-23

The [contract decision record](../../docs/youtube-worker-contract.md) contains the
verified caller, environment, Compose, deployment, broker and worker map, three
bounded options with migration/failure/test costs, and a concrete proposed
schema and exception policy for downstream tasks.

- Client uses `ytdlp.extract_info` and `ytdlp.download_video` over the broker API.
  Root Compose starts only the bot and loads `.env`; its template omits
  `BROKER_URL`.
- External `gakawarstone/gkbroker` at
  `1cd7dbde74c888053e32abebbaea08615585474a` defines `pending`, `processing`,
  `completed`, `failed`. Cancel deletes pending tasks; subsequent GET returns 404.
- Read-only inspection of the running local yt-dlp worker and its broker's
  OpenAPI confirms the broker protocol is in use outside GKBot Compose. The
  worker submits embedded error JSON through the success endpoint, so an outer
  `completed` status alone does not prove operation success.
- The production GKBot endpoint/worker revision remains unverified. No bot
  container is running locally, the audit shell has no `BROKER_URL`, and the root
  checkout's `.env` was not accessed. Owner confirmation is still required.
- Recommended option A retains the external broker and hardens the client.
  Option B adds a compatible local deployment. Option C requires a replacement
  protocol design because the removed supervisor is not compatible.

Owner decision: **PENDING**. Runtime/deployment files remain unchanged. The task
stays OPEN and must not be deleted until the owner explicitly selects the target
architecture and the decision is recorded. Downstream shared-helper and polling
runtime work must wait for that approval.

