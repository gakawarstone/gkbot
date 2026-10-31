# YouTube keyboard visual experiment

Evaluation date: 2026-10-23. Decision: **reject production styling for now**.
No client trial was completed. The task remains OPEN pending screenshots and
accessibility/fallback checks. Application behavior is unchanged.

## Candidate and decision

Use `YtdlpMarkup.get_download_dialog`, shown when a user sends a YouTube link.
It is a common media entry point, though usage rankings are not measured.
The current row is `Аудио`, `Видео`, `убрать`. Add `style="danger"` only to
`убрать`, keeping all labels, positions, and callbacks.

Red might distinguish message removal from downloading, but it adds no
information to the label and could suggest cancelling a download or deleting
a file. The callback only removes the dialog message. No observed benefit
justifies enabling the style. No style is accepted, so no shared helper is
needed. Any later accepted choice must use a shared keyboard helper.

## API and eligibility

[Telegram's button contract](https://core.telegram.org/bots/api#inlinekeyboardbutton)
defines optional `style` values `danger`, `success`, and `primary`, and
`icon_custom_emoji_id` for an icon before the label. Custom icons require an
additional bot username purchased on Fragment, or a Premium bot owner for
messages sent directly to private, group, and supergroup chats. The latter
route does not cover inline results or channel posts.

Neither eligibility nor an approved emoji ID was established for this bot.
Custom icons are excluded: existing text already labels every action. A
recipient's Premium status or emoji ID does not establish bot eligibility.

[aiogram 3.31.0](https://docs.aiogram.dev/en/v3.31.0/api/types/inline_keyboard_button.html)
exposes both fields. Merged PR [#11](https://github.com/gakawarstone/gkbot/pull/11)
supplies that version and a pinned Bot API 10.3 image. Follow the
[server compatibility checks](../services/bot-api/README.md); the deployed
server version was not verified by this evaluation.

## Offline candidate

Run after `uv sync --locked`. This prints markup without credentials or network
requests. Deep copying protects the shared delete button used by other keyboards.

```bash
PYTHONPATH=bot .venv/bin/python - <<'PY'
from ui.keyboards.ytdlp import YtdlpMarkup

before = YtdlpMarkup.get_download_dialog("abcdefghijk")
after = before.model_copy(deep=True)
after.inline_keyboard[0][2].style = "danger"
print(before.model_dump_json(exclude_none=True))
print(after.model_dump_json(exclude_none=True))
PY
```

The only payload difference is the third button's style. Omitting it restores
the current markup. Text labels remain available without color or custom icons;
this does not prove how older clients render unsupported fields. Omit fields
unsupported by the server or bot rather than relying on request rejection.

## Missing client evidence

No before/after screenshots were obtained. On 2026-10-23, Telegram Web snapshot
attempts timed out twice, and fallback computer access had no browsers or apps.
No authenticated client or controlled test chat was established. Payloads and
mockups do not satisfy the screenshot criterion.

To finish in a controlled chat:

1. Verify the test server and record each client version, OS, theme, and text
   size. No minimum supported client version was established here.
2. Capture the same dialog before/after on Telegram Desktop and a mobile client
   in light/dark themes, removing personal chat details from the images.
3. Compare audio/video selection and dialog removal, alternating presentation
   order. Record wrong taps and whether red suggests download cancellation.
4. Check screen reader labels/traversal, large text, focus, contrast, and
   readability without color. Capture the explicit unstyled fallback and test
   an identified older client if available. Verify the original callbacks.

Keep the reject decision unless observed selection improves without misleading
users or worsening accessibility/fallback behavior. Stop if the change is only
decorative. Keep the task OPEN until the required client evidence exists.
