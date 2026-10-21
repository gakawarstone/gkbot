# Render dates with Telegram date-time entities

- STATUS: OPEN
- PRIORITY: 4

## Problem

Reminder and task views format dates as fixed text. Telegram date-time entities can render a timestamp in the client's locale, but changing stored scheduling semantics would be a mistake. This task is limited to presentation.

## Plan

1. Check client support and rendering for the locales used by the bot.
2. Add a formatting helper that emits a `date_time` entity from a known Unix timestamp.
3. Use it in reminder and task summaries where the timestamp is unambiguous.
4. Keep a plain-text fallback.
5. Add timezone and entity-offset tests.

## Acceptance criteria

- Supported clients display reminder and task times in the user's locale.
- Scheduling and stored timezone calculations do not change.
- Entity offsets remain correct with surrounding Cyrillic text and emoji.
- Unsupported paths retain a readable date.

