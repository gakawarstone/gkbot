# Video covers and playback start positions

`services.video.VideoMetadata` adds optional keyword-only `cover` and
`start_timestamp` fields to `VideoFileInfo`, `InfoVideoTikTok`, and `TikTokVideo`.
Existing positional constructors still work. `send_options(duration)` returns
only usable optional Telegram arguments. It accepts HTTP/HTTPS JPEG or PNG
cover URLs and `InputFile` uploads. URL validation rejects credentials, malformed
ports, whitespace, and unsupported image extensions. Unknown formats are omitted
rather than guessed.

The yt-dlp provider maps `thumbnail` to `cover` and `start_time` to
`start_timestamp`, for both local extraction and worker metadata. When the
preferred thumbnail is WebP or invalid, it tries the thumbnail list from best to
worst. Candidates explicitly requiring request headers are skipped. No extra
provider request is made just to obtain these fields. yt-dlp can expose covers
for YouTube, VK, TikTok and other extractors; the fields remain optional because
availability depends on the particular video. TikTok's yt-dlp fallback carries
the metadata through the existing extractor and service contracts. Other TikTok
extractors and raw feed video URLs keep their previous behavior.

Only a provider playback offset is used. Upload/publication timestamps, chapter
starts and dates are never substituted. Finite nonnegative numeric offsets are
rounded down to whole seconds. Booleans, strings, values beyond a signed 32-bit
integer and offsets at or after a known duration are omitted. A missing duration
does not rule out an offset; the duration is checked again before sending, after
any ffprobe fallback. Offsets are omitted when download options remove sponsor
segments, because source offsets no longer identify the same point in the output.
This includes ordinary YouTube downloads with the current options. YouTube
Shorts and other unedited downloads can retain their source offset.

`VideoFeedItemView._send_video_item` handles the common feed send. TikTok feed
views pass provider-neutral metadata to it. Download buttons, short-video
messages and TikTok messages use the same `ui.video.send_video` helper. Existing
captions, dimensions, duration, thumbnails, streaming and spoiler arguments are
preserved. If Telegram returns `TelegramBadRequest` while optional metadata is
present, the helper retries once without both optional fields. This handles
expired covers and Bot API servers that reject the fields. A second failure
propagates. Network failures are not retried, to avoid duplicate successful sends.
Without usable metadata, the helper sends the original arguments once.

The API contract was checked against installed aiogram 3.31.0 and yt-dlp
2026.8.19. See [Telegram sendVideo](https://core.telegram.org/bots/api#sendvideo)
and the [yt-dlp extractor metadata contract](https://github.com/yt-dlp/yt-dlp/blob/2026.08.19/yt_dlp/extractor/common.py).

Run the unit coverage with:

```sh
make test FILE='bot/tests/services/test_video_metadata.py bot/tests/services/test_ytdlp_video_metadata.py bot/tests/handlers/test_video_metadata.py'
```

These tests exercise timestamp bounds, malformed provider payloads, cover
selection, local/worker parsing, ffprobe preservation, edited timelines and
bounded fallback without retries after network failures.
They do not require Telegram credentials or a running download worker.
