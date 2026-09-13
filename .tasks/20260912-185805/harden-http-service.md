# Harden the shared HTTP service

- STATUS: OPEN
- PRIORITY: 2

## Problem

The shared HTTP wrapper creates a new `aiohttp.ClientSession` for each request, disables connection timeouts in several methods, and returns 4xx and 5xx bodies as successful responses. Exception handling differs by method, so callers may receive raw aiohttp, JSON, and decoding errors instead of one useful service error.

## Plan

1. Manage one application-scoped client session with explicit connect, read, and total timeouts.
2. Check response status before reading or decoding the body.
3. Define which aiohttp and decoding failures become `HttpRequestError` and retain their causes.
4. Add response-size limits for endpoints that load whole bodies into memory.
5. Close the shared session during bot shutdown.
6. Add tests for success, redirects, 4xx, 5xx, timeout, invalid JSON, connection failure, and oversized bodies.

## Acceptance criteria

- All shared HTTP methods enforce finite timeouts and reject error statuses.
- Callers receive consistent typed failures with the original cause attached.
- The bot reuses and closes its HTTP session.
- Tests cover each public HTTP method's failure behavior.

