# Reminder date presentation

The reminder confirmation sends a `date_time` entity once the form contains a
date, a time, and the user's stored UTC offset. It uses the same
`datetime.combine(date, time, timezone(offset))` calculation as
`CreateRemindHandler.datetime`. The scheduler, timezone storage, and notification
contents are unchanged.

`ui.date_time.format_date_time(unix_time, fallback)` creates an aiogram `DateTime`
node with format `dt`. Compose this node with `Text` and send `as_kwargs()` so
aiogram computes UTF-16 offsets and explicitly disables the bot's default HTML
parse mode. Keep the date node outside other formatting entities. User reminder
text is literal text, including `<`, `>`, and `&`.

## Client support and fallback

Telegram introduced client date formatting on
[March 1, 2026](https://telegram.org/blog/member-tags-disable-sharing-and-more).
The [client rendering contract](https://core.telegram.org/api/entities#date-entities)
specifies the viewer's timezone and locale for short date and time rendering.
The bot uses Russian interface text, but sends no locale-specific date pattern.
Russian, English, and other client locales all receive the same timestamp and
`dt` format. A viewer whose device timezone differs from their stored bot offset
sees the corresponding local time, while delivery still uses the stored offset.

The [Bot API format](https://core.telegram.org/bots/api#date-time-entity-formatting)
is supported by the pinned aiogram 3.31.0 and Bot API 10.3 configuration. Use that
server configuration before enabling the updated bot. Client support is based on
Telegram's published contract; on-device rendering was not tested in this change.

The message still contains a complete fixed-text date, for example
`01.01.2027 00:15 UTC+0530`. Clients that ignore the entity can display that text.
Incomplete input or a missing timezone uses ordinary text. Dates outside
Telegram's supported Unix range, from zero through 1098 days ahead, also remain
text. The helper rejects empty fallback spans and spans longer than Telegram's
31 UTF-16-unit limit. `RemindCreator.render()` retains HTML with fixed-text dates
for callers that cannot send entities.

Notion task views are retired by
[PR #25](https://github.com/gakawarstone/gkbot/pull/25) and receive no new rendering.
The remaining timer views show durations, and road habit inputs contain only a
time of day. Neither identifies an absolute instant suitable for this entity.

## Verification

Run the focused presentation, handler, and scheduling checks:

```sh
make test FILE='bot/tests/ui/test_date_time.py bot/tests/handlers/test_reminder_dates.py bot/tests/services/test_reminder.py bot/tests/services/test_schedule.py'
```

These check UTC offsets from -12 to +14, fractional offsets, crossing midnight,
the stored timestamp, Cyrillic and emoji offsets, literal user text, incomplete
forms, and fallback limits. No test connects to Telegram.

For a manual client check, create a reminder for `01.01.2027 00:15` with stored
offset `UTC+05:30`. In Russian and English clients, verify that the date uses the
client's date/time preferences. With a device timezone of UTC it must represent
`31.12.2026 18:45`; with UTC+05:30 it must represent `01.01.2027 00:15`. Check that
the success status is still underlined and the reminder text, including emoji,
is unchanged. A client that ignores the entity must retain the full fallback.
