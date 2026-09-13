# Edit a status message into single media

- STATUS: OPEN
- PRIORITY: 3

## Problem

The Instagram path sends a text status, sends downloaded media as a new message, then deletes the status. Bot API supports replacing a text message with media, which can remove one send and one delete for single-item results.

## Plan

1. Restrict the new path to a single photo or video that Telegram can use in `editMessageMedia`.
2. Edit the existing status message into the final media response.
3. Keep the current media-group path for albums and a send-then-delete fallback for edit failures.
4. Preserve captions, parse mode, dimensions, and thumbnails.
5. Add tests for single photo, single video, album, and failed edit.

## Acceptance criteria

- A successful single-item Instagram download reuses its status message.
- Albums still use the current media-group behavior.
- An edit failure sends the media normally and cleans up the status when possible.
- Instagram handler tests pass.

