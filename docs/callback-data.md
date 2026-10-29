# Download callback data

All six families use aiogram `CallbackData.pack()`, `unpack()` and typed filters.
`download(callback, callback_data=None)` accepts an injected model or validates
raw data for direct callers before source requests or status messages.

| Source | Prefix and separator | Fields in wire order |
| --- | --- | --- |
| YouTube | `ytbtn`, `:` | action, status, yt_video_code |
| VK | `vk2`, `\|` | action, status, reference_kind, reference_value |
| Pornhub | `phbtn`, `:` | action, status, ph_video_code |
| Porno365 | `p365v2`, `\|` | action, status, page_url |
| Matreshka | `matreshkabtn`, `:` | video_id |
| Sasflix | `sasflixbtn`, `:` | topic_uuid |

Actions are `dlmp3` for audio and `dlmp4` for video. Pornhub and Porno365 accept
only video. Native status values are `0` and `1`; exact `False` and `True` also
remain readable. Aliases, empty values and unknown actions are rejected. Status
is required because aiogram would replace an empty component with a field default.

IDs remain opaque nonempty strings without whitespace. Sasflix packs UUIDs in
compact form and accepts existing hyphenated UUIDs. Packing rejects embedded
separators and payloads above Telegram's 64 UTF-8 byte limit. VK/Porno365 use `|`
so full URLs retain their colons; a literal pipe in a value is rejected.

VK uses scalar `reference_kind` and `reference_value` because native packing does
not support a domain dataclass. Kinds are `identifier` and `short_url`; the pair
must form a valid [VKReference](vk-references.md). Full wall post IDs and short
URL query strings are preserved.

## Existing messages

Already-sent keyboards persist, so the read-only compatibility bridge has no
automatic expiry. YouTube, Pornhub, Matreshka and Sasflix retain native decoding
of their valid old payloads. The bridge reads exact `vkbtn:` and `p365btn:`
prefixes, splits at most three colons to preserve URLs, and requires legacy
`True`/`False` status before validating the same target models. New buttons never
emit these two old formats. Removing support requires a separate decision about
existing messages; malformed values are not part of that compatibility contract.

The [shared lifecycle](download-callbacks.md) continues to own media/status work
and cleanup. Carousel callbacks remain outside this protocol.
