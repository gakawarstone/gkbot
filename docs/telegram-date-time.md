# Reminder dates

Reminders keep their stored UTC offset for scheduling. Telegram clients display
that same instant in the viewer's locale and device timezone. The underlying
text includes the entered date, time, and UTC offset for clients without date
formatting. Incomplete input and dates outside Telegram's accepted range remain
plain text.

`format_date_time(unix_time, fallback)` returns an aiogram `Text` node. Compose it
outside other formatting entities and send `as_kwargs()` to preserve UTF-16
offsets and disable the default HTML parse mode. `RemindCreator.render()` keeps
the fixed-text HTML path used by existing callers.

The [Telegram rendering contract](https://core.telegram.org/api/entities#date-entities)
and [Bot API format](https://core.telegram.org/bots/api#date-time-entity-formatting)
define date limits and localization. Use the pinned Bot API 10.3 configuration.
On-device rendering has not been tested in this change.

For a manual check, create a reminder for `01.01.2027 00:15` with stored offset
`UTC+05:30`. Russian and English clients should use their date/time preferences.
A UTC device should show `31.12.2026 18:45`; a UTC+05:30 device should show
`01.01.2027 00:15`. A client that ignores the entity should retain the full
fallback, and reminder text containing emoji or HTML-like characters should
remain unchanged.
