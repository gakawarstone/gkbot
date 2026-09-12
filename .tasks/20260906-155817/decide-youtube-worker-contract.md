# Decide the YouTube worker contract

- STATUS: OPEN
- PRIORITY: 2

## Problem

The YouTube downloader expects an external broker with `/enqueue` and `/result/<task_id>`. Root Compose does not provide that service, while the repository's worker supervisor exposes `/upload` and `/fetch`. The intended deployment contract is unclear.

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

