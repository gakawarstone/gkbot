# Download callback contract

The YouTube, VK, Pornhub and Porno365 `download(callback)` entry points use
`handlers.button.download.handle_download(callback, prepare_request, *,
raise_on_invalid_callback=False)`.

The helper checks for an accessible message and non-`None` data before awaiting
`prepare_request(raw_callback_data)`. VK enables `raise_on_invalid_callback` to
retain its `ValueError` behavior; other sources return for invalid callbacks.

The adapter returns `DownloadRequest`:

- `url`: resolved URL. Porno365 resolves its page URL before status creation;
  VK uses `reference.download_url`.
- `media_type`: `"audio"`, `"video"`, or `None` for the legacy status-only path.
- `use_callback_message_as_status`: reuse and delete the callback message when
  true; otherwise create and delete a separate status message.
- `video_options`: optional `caption`, `thumbnail` and `has_spoiler` values.
- `prepare_video`: optional async `(url, VideoFileInfo) -> VideoOptions` hook.
  It runs inside the downloader context before sending; returned values override
  static options without mutating the request.

Media stays inside the downloader context until sending finishes. Status deletion
runs in `finally`, including failures and cancellation. Errors propagate. Parsing
and URL resolution failures occur before status creation.

## Legacy callback compatibility

| Source | Payload |
| --- | --- |
| YouTube | `ytbtn:dlmp3:<status>:<code>` or `ytbtn:dlmp4:<status>:<code>` |
| VK | `vkbtn:dlmp3:<status>:<reference>` or `vkbtn:dlmp4:<status>:<reference>` |
| Pornhub | `phbtn:dlmp4:<status>:<code>` |
| Porno365 | `p365btn:dlmp4:<status>:<page_url>` |

Serializers emit `True`/`False`; legacy decoders treat only `False` as false.
VK and Porno365 retain colons in URLs by splitting at most three times.
CallbackData migration belongs in adapters and registration, keeping this request
contract. Carousel callbacks are outside this helper.
