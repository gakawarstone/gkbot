# Download callback lifecycle

YouTube, VK, Pornhub and Porno365 use `handlers.button.download.handle_download`.
Their `download(callback, callback_data=None)` entry points stay in
`handlers.button.<source>.download`.

## Adapter contract

`handle_download(callback, prepare_request, *, raise_on_invalid_callback=False)`
checks that the callback has an accessible message and non-`None` data, then
awaits `prepare_request(raw_callback_data)`. The adapter returns a typed
`DownloadRequest` with these fields:

- `url`: resolved download URL. Porno365 resolves its page URL before creating
  the status message. VK uses `reference.download_url` from the prerequisite
  `VKReference` model.
- `media_type`: `"audio"`, `"video"`, or `None`. `None` preserves the legacy
  status-only path for an unknown event.
- `use_callback_message_as_status`: edit and later delete the callback message
  when true; otherwise send and later delete a separate status message.
- `video_options`: optional `caption`, `thumbnail` and `has_spoiler` values.
- `prepare_video`: optional async hook taking `(url, VideoFileInfo)` and returning
  additional `VideoOptions`. It runs inside the downloader context, before
  sending the video. Hook options override static options.

The helper owns the status text, audio/video downloader contexts, media dispatch
and status deletion. Media is sent while the downloader context is active, so
its input file remains available until Telegram finishes sending. Status deletion
runs in `finally`, including download, metadata, send failures and cancellation.
Exceptions propagate to the caller. Parsing and URL resolution failures occur
before any status message is created.

VK passes `raise_on_invalid_callback=True`, retaining its existing `ValueError`
messages for missing/inaccessible messages and missing data. Other sources
return without work for these callbacks.

## Source behavior

| Source | URL and options |
| --- | --- |
| YouTube | `https://www.youtube.com/watch?v=<code>`; video caption uses the downloaded title and the channel name with emoji removed; thumbnail comes from `YoutubeApiService` |
| VK | `reference.download_url`; no extra video options |
| Pornhub | `https://www.pornhub.com/view_video.php?viewkey=<code>`; video spoiler enabled |
| Porno365 | `Porno365Service.get_best_video_url(page_url)`; video spoiler enabled |

Audio retains the downloaded title, duration and `performer="GKBOT"`. Video
retains height, width, duration and `supports_streaming=True`. Only YouTube and
VK support audio.

## Callback compatibility and migration

The six download button families now use typed aiogram CallbackData filters.
Adapters accept the injected model and retain raw-payload validation for direct
`download(callback)` callers. New VK/Porno365 buttons use a pipe separator;
existing messages remain supported through a strict legacy filter. All boolean
and action fields are validated before URL resolution or status creation.
Unknown events no longer reach the former status-only path. The generic helper
still accepts `media_type=None` for other callers.

See [callback data](callback-data.md) for prefixes, fields and compatibility.
Carousel callbacks are outside this contract.

## Tests

`make test FILE=bot/tests/handlers/button/test_download.py` runs the same lifecycle
contract across all supported source/media combinations. It checks status modes,
source options, legacy payloads, invalid callbacks, router registration, failure
cleanup and cancellation. The four previous YouTube/VK integration smoke tests
are retained as one opt-in parametrized test in that module.
