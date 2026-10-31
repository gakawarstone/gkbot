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

## Decision pending

The [decision record](../../docs/youtube-worker-contract.md) contains the verified
2026-10-23 contract map, alternatives and proposed downstream policy. Recommendation
is A, retain the external broker. Production pairing and the owner's architecture
selection remain unconfirmed. Keep this task OPEN and downstream runtime work
blocked until the owner selects an option and the decision is recorded.
