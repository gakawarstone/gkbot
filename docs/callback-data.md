# Download callback data

All six download button families use `aiogram.filters.callback_data.CallbackData`.
Their builders call native `.pack()`, and their routers use native `.filter()`.
The handler receives a validated `callback_data` model. Direct calls to
`download(callback)` remain supported and validate the raw payload before any
service request or status message.

## Wire formats

| Source | Prefix and separator | Fields in wire order |
| --- | --- | --- |
| YouTube | `ytbtn`, `:` | action, status, yt_video_code |
| VK | `vk2`, `\|` | action, status, reference_kind, reference_value |
| Pornhub | `phbtn`, `:` | action, status, ph_video_code |
| Porno365 | `p365v2`, `\|` | action, status, page_url |
| Matreshka | `matreshkabtn`, `:` | video_id |
| Sasflix | `sasflixbtn`, `:` | topic_uuid |

Models live in `bot/ui/buttons/`, with shared types in `download.py`.
`DownloadAction` is a string enum with `dlmp3` for audio and `dlmp4` for video.
Pornhub and Porno365 validate that the action is video. Unknown actions are
rejected before any work, including the former status-only path.

Status is a required boolean field. Native packing emits `0` or `1`; unpacking
also accepts exact `False` or `True` for existing buttons. Empty values, lowercase
aliases, `yes`, `no`, `on`, `off`, whitespace and arbitrary numbers are rejected.
The field intentionally has no default, since aiogram substitutes defaults for
empty wire components. Keyboard producers supply false for feed buttons and true
for YouTube/VK download dialogs.

IDs stay strings and cannot be empty or contain whitespace. Sasflix uses a UUID
field; native packing emits compact UUIDs, while unpacking accepts existing
hyphenated UUIDs. The service URL retains its usual hyphenated representation.
CallbackData rejects embedded separators and outgoing payloads above 64 UTF-8
bytes. Full URLs in VK and Porno365 fields retain their colons because the new
separator is `|`. A literal pipe in a field is rejected, not escaped or truncated.

VK stores scalar `reference_kind` and `reference_value` fields because native
CallbackData does not pack a domain dataclass. Both fields are checked by the
`VKReference` constructor. The model's `.reference` property exposes the validated
domain value, and `from_reference(reference, action=..., ...)` constructs the
callback model. Full `wall-owner_post` references and short URL query strings are
preserved. See [VK references](vk-references.md).

## Existing Telegram messages

Existing messages retain their inline keyboards, so this migration keeps a
read-only compatibility path with no automatic expiry.

- YouTube/Pornhub retain their prefixes and field order. Native unpacking plus the
  strict status validator reads their old payloads directly.
- Matreshka retains its format. Sasflix reads existing valid UUID payloads.
- `ui.buttons.compatibility` reads only exact `vkbtn:` and `p365btn:` prefixes.
  Its legacy filter validates the action, exact `True`/`False` status and target,
  then injects the same typed model as the native filter. Splitting the old wire
  format at most three times preserves URL colons. VK values pass through
  `parse_vk_reference`; malformed or unsupported references are rejected.

The compatibility module is the only manual read path. New builders never emit
old VK/Porno365 payloads. The former per-family serializer/deserializer classes
and prefix helpers are removed. Remove the legacy bridge in a separate change
only after deciding how to handle previously sent messages; their age cannot be
inferred from the callback itself. Previously accepted malformed input is not a
compatibility contract.

## Lifecycle and scope

The migration is stacked on the VK references PR #13 and lifecycle PR #15.
Source adapters still return `DownloadRequest` to the shared lifecycle, which owns
status, media dispatch and cleanup. Captions, thumbnails, spoilers, timeouts and
source URL resolution are preserved. See [download lifecycle](download-callbacks.md).

Carousel callbacks are outside this migration. Their `item_id` stays an opaque
string under the adjacent TODO audit's `BaseCarouselMarkup.get_item_markup`
contract. This migration does not integrate the duplicate lifecycle PR #24.

## Validation

Offline tests cover all six model round trips, literal old payloads, malformed
field counts/prefixes, action and reference enums, strict booleans, UUIDs,
separator rejection and the 64-byte boundary, including multibyte IDs. Router
tests verify rejection through the real router and handlers. Dialog tests retain
the target and status-reuse contract. The lifecycle contract exercises
both old and new payloads through the registered routers.

Run `make test FILE='bot/tests/ui/buttons bot/tests/handlers/button'` for focused
coverage and `make test` for the offline suite. Telegram integration smoke tests
remain opt-in. API behavior was checked against the installed aiogram 3.31.0 and
its [official implementation](https://github.com/aiogram/aiogram/blob/v3.31.0/aiogram/filters/callback_data.py).

On the synchronized lifecycle base `7424a99` with aiogram 3.31.0, the full
offline suite passes with 340 passed and 13 skipped; focused callback/lifecycle
checks pass with 156 passed and 4 skipped. Scoped Ruff, typos, format and Pyright
pass for all 26 changed Python files. `make lint` stops at the existing imported
Mypy error in `bot/handlers/prompt/generate_image.py:43`; that file, `pyproject.toml`
and `uv.lock` match the used dev base. Mypy with `--follow-imports=silent` passes
all 26 changed files. The integration preserves both layers' test removals and
the callback migration's production behavior; it adds no test scenarios.
