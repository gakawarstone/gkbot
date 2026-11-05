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
The handler uses `reference.download_url`; see [callback data](callback-data.md)
for the wire format and compatibility with existing buttons.

`get_vk_id(url)` and `reconstruct_vk_url(value)` remain compatibility adapters
for supported references. Both use the same parser and raise `ValueError` for
unsupported input. New consumers should use the domain value.
