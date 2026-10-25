# Replace Similar callback with a disabled button

- STATUS: OPEN
- PRIORITY: 1

## Problem

The feed keyboard advertises a Similar action, but its callback branch is a stub and does not select items from the requested feed. Telegram Bot API 10.3 supports native disabled inline buttons, while the project pins `aiogram==3.26.0`, which does not expose that field.

## Plan

1. Complete the aiogram 3.31 upgrade task with typed Bot API 10.3 support.
2. Render Similar as `InlineKeyboardButton(disabled=DisabledButton())`.
3. Replace other display-only callbacks such as carousel page indicators with disabled buttons.
4. Remove obsolete callback values, branches, and commented implementations that only support those placeholders.
5. Update keyboard and callback tests.

## Acceptance criteria

- Similar remains visible but cannot send a callback.
- No `show_all_feed` callback branch remains.
- Dependency and lock files agree on the aiogram version.
- The full unit test suite and static checks pass.

## Implementation status, 2026-10-22

Prerequisite PR #11 has merged into `dev-3.0`. The 2026-10-25 conflict
resolution merged dev commit `2db43ed99af695c841ed7c29194df88da8d42225`
into this branch and retargets PR #16 to `dev-3.0`. This PR remains draft;
client evidence and production approval are still required.

- Similar remains visible as `Похожие` and serializes as
  `{"text": "Похожие", "disabled": {}}`, without callback data.
- Carousel page numbers use the same disabled type; navigation callbacks and
  first/last/single-item behavior are preserved.
- Removed the `show_all_feed` callback constant, branch, and commented
  implementation. Old Similar callbacks and unknown feed actions no longer
  select a random next item or cause message/API deletion.
- Kept the `feed_id` markup argument for compatibility with existing callers.
- After the 2026-10-25 test review, retained one existing stale-Similar
  regression. Removed serialization snapshots, mock-call choreography, and a
  duplicate unknown-action case. The remaining check observes chat/feed state
  using the real handler and picker with fakes at external service boundaries.

### Verified API contract

[Telegram InlineKeyboardButton](https://core.telegram.org/bots/api#inlinekeyboardbutton)
requires exactly one action field. `disabled` is a
[DisabledButton](https://core.telegram.org/bots/api#disabledbutton), an empty
object, not a boolean. The
[aiogram 3.31 API](https://docs.aiogram.dev/en/latest/api/types/inline_keyboard_button.html)
exposes this typed field. Official PyPI wheel inspection confirmed it is
absent in 3.26.0 and present in 3.31.0. All four dependency files agree on
3.31.0 through the prerequisite commits.

### Validation and remaining acceptance criteria

- Validation after the dev merge on 2026-10-25: focused regression passed;
  full suite 162 passed, 13 skipped.
- The retained regression fails if the callback guard is removed in memory:
  the stale button sends an unwanted exhaustion reply to the chat. No
  production file was modified for this check.
- Targeted `make lint FILE=...`: Ruff, typos, mypy, and pyright passed for
  the three changed production files and retained regression. Import ordering
  from merged PR #32 is preserved; the merge left one unused `Any` import,
  which was removed.
- `uv lock --check`, `uv pip check`, and `git diff --check` passed.
- Global `make lint` stops at 196 Ruff findings versus 204 at the used dev
  commit. Comparing structured diagnostics shows no introduced findings;
  the eight removed findings belong to the three changed production files.
  The later global lint stages do not run after Ruff fails.

The task remains OPEN because the full static checks do not pass and the
required server rollout has not happened. Do not remove this task file yet.
The currently deployed `gkbot-api` is Bot API 9.5 according to the prerequisite
owner's isolated binary check. The pinned image reports Bot API 10.3, but an
image pin does not update the running server. An operator must roll out 10.3
before deploying the upgraded client or these keyboard changes. This thread
performs no production rollout. See `services/bot-api/README.md` for rollout
order and the remaining live keyboard checks.
