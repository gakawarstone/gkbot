# YouTube keyboard visual experiment

Evaluation date: 2026-10-23. Decision: **reject production styling for now**.
The client experiment is blocked, so this is a design and serialization review,
not a completed usability trial. Keep the existing keyboard and keep the task
open until the required client screenshots and checks exist.

## Scope and hypothesis

Use `YtdlpMarkup.get_download_dialog`, shown when a user sends a YouTube link
through `bot/handlers/text/ytdlp.py`. This is a common media entry point; the
repository has no usage measurements establishing which keyboard is most used.
Do not extend the experiment to feed keyboards or other handlers.

The current keyboard has one row: `Аудио`, `Видео`, `убрать`. The candidate adds
`style="danger"` only to `убрать`. Keep its text, position, and `del_msg`
callback. Leave audio and video equally prominent. The hypothesis is that red
makes the message removal action easier to distinguish from downloading.

This candidate is small enough to reject without changing application code.
The existing `убрать` callback deletes the dialog message. It does not cancel
a download or delete a downloaded file. Color must not imply those actions.

## API and eligibility evidence

[Telegram's button contract](https://core.telegram.org/bots/api#inlinekeyboardbutton)
defines `style` values `danger`, `success`, and `primary`; omitting the field
uses the client's default. It also defines `icon_custom_emoji_id` as a separate
icon before the button label.

Custom icons require a bot with an additional username purchased on Fragment,
or a Premium bot owner for messages the bot sends directly to private, group,
and supergroup chats. A recipient's Premium status does not establish the
owner's eligibility. The latter route does not cover inline results or channel
posts. No evidence for either eligibility route, or an approved emoji ID, was
provided for this bot. Eligibility remains **unverified**. Do not send custom
emoji IDs taken from a user's Premium messages.

[aiogram 3.31.0's button model](https://docs.aiogram.dev/en/v3.31.0/api/types/inline_keyboard_button.html)
exposes both fields as optional strings. The installed 3.31.0 model and the
serialization example below were checked locally. Model construction proves
neither Telegram server acceptance nor client rendering. There is no client
version capability field in the button model to select a rendering fallback.

PR [#11](https://github.com/gakawarstone/gkbot/pull/11) is merged and supplies
aiogram 3.31.0 and a pinned Bot API 10.3 image. See
[server compatibility and rollout checks](../services/bot-api/README.md).
A merged image pin does not prove the deployed server version; this evaluation
does not redeploy or claim to verify the running service.

Custom icons are excluded from the candidate. They would add decoration to
already explicit text and introduce an eligibility dependency without a
demonstrated clarity benefit. Reconsider them only with eligibility evidence,
an approved ID, and a concrete user problem.

## Reproduce the candidate without contacting Telegram

Run from this worktree after `uv sync --locked`. The example uses the real
keyboard builder and prints markup only. It does not create a bot, load
credentials, or send messages.

```bash
PYTHONPATH=bot .venv/bin/python - <<'PY'
import json

import aiogram
from aiogram.types import InlineKeyboardButton
from ui.keyboards.ytdlp import YtdlpMarkup

assert aiogram.__version__ == "3.31.0"
assert {"style", "icon_custom_emoji_id"} <= InlineKeyboardButton.model_fields.keys()

before = YtdlpMarkup.get_download_dialog("abcdefghijk")
after = before.model_copy(deep=True)
after.inline_keyboard[0][2].style = "danger"

before_payload = before.model_dump(exclude_none=True)
after_payload = after.model_dump(exclude_none=True)
expected = json.loads(json.dumps(before_payload))
expected["inline_keyboard"][0][2]["style"] = "danger"
assert after_payload == expected

fallback = after.model_copy(deep=True)
for row in fallback.inline_keyboard:
    for button in row:
        button.style = None
        button.icon_custom_emoji_id = None
assert fallback.model_dump(exclude_none=True) == before_payload

print(json.dumps({"before": before_payload, "after": after_payload},
                 ensure_ascii=False, indent=2))
PY
```

For the fixture code `abcdefghijk`, the original callbacks are
`ytbtn:dlmp3:True:abcdefghijk`, `ytbtn:dlmp4:True:abcdefghijk`, and `del_msg`.
The only payload difference is `"style": "danger"` on the third button.
Deep copying avoids mutating the shared delete button object used by other
keyboards.

Removing the new fields reproduces the current markup exactly. All actions
retain Russian text, so neither color nor a new icon carries the only label.
This checks the application's fallback payload, not how an older Telegram
client handles unknown fields. If the server or bot is not eligible for a
field, omit that field before sending; do not assume a rejected request will
produce a usable keyboard. Since no styles are enabled in production by this
change, current sends continue to use the existing markup.

## Clarity and accessibility review

The candidate adds no new information to `убрать`. It may separate message
removal from format selection, but may also suggest a more destructive action
than removing the dialog. Those are hypotheses, not observed user responses.
The current audio and video labels already distinguish the download formats.

Retaining every label and the row order preserves the text available to
assistive technology. Screen reader announcements, focus order, large text
clipping, contrast, and color vision accessibility still need client checks.
Do not infer those properties from the serialized JSON or a CSS mockup.

## Client evidence and remaining procedure

No before or after screenshots were obtained. T3 preview opened
`https://web.telegram.org/a/`, but both snapshot attempts failed with
`Preview automation snapshot timed out after 15000ms.` The fallback computer
inventory returned no browsers or native apps. No authenticated client or
controlled test chat was established. Do not count a web mockup, login screen,
or these payloads as the required screenshots.

To finish the experiment in a controlled chat:

1. Verify the test server version and record the client name, exact version,
   operating system, theme, and text size. Start with current Telegram Desktop
   and a current mobile client. Call a client supported only after observing
   the candidate's style there; no minimum client version was established here.
2. Use the same YouTube link and the example's two markups. Capture the whole
   dialog before and after, in light and dark themes. Store anonymized images
   beside this report, with the client details and observations. Crop personal
   chat details, not labels or keyboard edges.
3. On each client, ask users to choose audio, choose video, and remove the
   dialog. Record incorrect taps and whether they interpret red as cancelling
   a download. Alternate the presentation order. Keep all other text fixed.
4. Check large text, screen reader labels and traversal, focus visibility where
   applicable, and readability without relying on red. Record actual results.
5. Capture the explicit fallback with both new fields omitted. Also test an
   identified older client if available and record its actual behavior. Do not
   assume silently ignored fields. Check that each callback still reaches the
   original action in the controlled environment.
6. Accept a style only if observed selection improves without misleading users
   or worsening accessibility or fallback behavior. If the difference is only
   decorative, stop and keep the current keyboard.

Keep the present reject decision unless that evidence supports changing it.
No production style is accepted, so no new shared style helper or per-handler
style constants are added. If a later trial accepts a choice, put it in a shared
keyboard helper and preserve unstyled output as the default before enabling it.

The screenshot and client rendering acceptance criteria remain unverified.
The task must not be deleted on the strength of this report alone.

## Local validation

- Executed the example above with the locked aiogram 3.31.0 environment.
  The candidate differs only by the third button's style; stripping the new
  fields restores the original payload. Local documentation links resolve.
- `make test FILE=bot/tests/ui/buttons/youtube/test_download.py`: 3 passed.
- `make lint FILE=bot/ui/keyboards/ytdlp.py`: stops at one existing Ruff
  `I001` import ordering finding in the unchanged keyboard file. Later lint
  stages do not run. This documentation change does not fix unrelated lint.
- `git diff --check`: passed. No application Python files changed.
