# Send video covers and start timestamps

- STATUS: OPEN
- PRIORITY: 3

## Problem

Video handlers send dimensions, duration, and sometimes a thumbnail, but the shared video model does not carry a dedicated cover or playback start timestamp. Telegram clients can use both fields to present downloaded and feed videos better.

## Plan

1. Identify download providers that expose a reliable cover and useful start timestamp.
2. Add optional cover and start timestamp fields to the shared video metadata model.
3. Pass the fields through the common feed video view before changing individual handlers.
4. Omit invalid, missing, or unsupported metadata without failing the send.
5. Add model and send-argument tests.

## Acceptance criteria

- Videos with available metadata use the expected cover and start position.
- Videos without that metadata behave exactly as they do now.
- Provider-specific parsing does not leak into Telegram view classes.
- Video handler tests pass.

