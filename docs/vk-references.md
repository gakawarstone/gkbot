# VK references

`utils.vk.parse_vk_reference(text)` returns a frozen `VKReference` with these fields:

| Field | Meaning |
| --- | --- |
| `kind` | `VKReferenceKind.IDENTIFIER` or `VKReferenceKind.SHORT_URL` |
| `value` | A media identifier or an unresolved `https://vk.cc/...` URL |
| `download_url` | The final URL passed to the downloader |

Constructing `VKReference(kind, value)` validates that the value matches its kind.
Unsupported input raises `ValueError`.

```python
from utils.vk import VKReferenceKind, parse_vk_reference

reference = parse_vk_reference("https://vkvideo.ru/video-123_456")
assert reference.kind is VKReferenceKind.IDENTIFIER
assert reference.value == "video-123_456"
assert reference.download_url == "https://vk.com/video-123_456"

reference = parse_vk_reference("https://vk.cc/abc-123")
assert reference.kind is VKReferenceKind.SHORT_URL
assert reference.download_url == "https://vk.cc/abc-123"
```

The parser accepts `wall-<owner>`, `wall-<owner>_<post>`, and
`video-<owner>_<video>` identifiers with negative owner IDs. It also accepts
HTTPS media links on `vk.com` and `vkvideo.ru`, short links on `vk.cc`, and
supported links embedded in message text. Full media URLs become identifiers;
short URLs keep their query string and fragment. Parsing performs no network
requests.

Wall references keep the post ID. The old identifier extraction accidentally
removed the `_<post>` suffix.

## Button compatibility

`VKDownloadButtonCallbackData.reference` exposes a validated `VKReference`.
Construct it with `VKDownloadButtonCallbackData.from_reference(reference,
action=DownloadAction.video, use_callback_message_as_status=False)`.
The native wire format is `vk2|<action>|<0-or-1>|<reference_kind>|<reference_value>`.
The legacy compatibility filter still reads
`vkbtn:<dlmp3-or-dlmp4>:<True-or-False>:<reference.value>` and normalizes it to the
same typed model. It splits at the first three colons, preserving short URLs
and old buttons with owner-only wall identifiers. The download handler reads
`reference.download_url` directly. See [callback data](callback-data.md).

`get_vk_id(url)` and `reconstruct_vk_url(value)` remain compatibility adapters
for supported references. Both use the same parser and raise `ValueError` for
unsupported input. New consumers should use the domain value.
