# Upgrade aiogram to 3.31

- STATUS: OPEN
- PRIORITY: 1

## Problem

The project pins `aiogram==3.26.0`. Message draft stop controls, rich messages, ephemeral messages, and native disabled buttons require newer aiogram releases and Telegram Bot API versions up to 10.3. The local Bot API image uses a floating `latest` tag, so package support and server support can drift apart.

## Plan

1. Check the deployed Telegram Bot API server version and confirm support for Bot API 10.3.
2. Pin the Bot API container to a known compatible version instead of `latest`.
3. Upgrade aiogram directly to 3.31.0 or a newer tested patch release.
4. Regenerate `uv.lock`, `requirements.txt`, and `requirements-dev.txt` through the project tooling.
5. Update test doubles for any new methods and required model fields exposed by the upgrade.
6. Run the full unit suite, lint checks, and smoke tests for polling, callbacks, HTML messages, and `/admins`.

## Acceptance criteria

- All dependency files resolve to the same aiogram version.
- The Bot API server version is pinned and supports every enabled aiogram feature.
- Existing polling, callback, media, AI chat, and administrator flows still work.
- `make test` and `make lint` pass.

