# Video covers and playback start positions

`VideoFileInfo`, `InfoVideoTikTok`, and `TikTokVideo` share optional keyword-only
`cover` and `start_timestamp` fields. Existing positional constructors still work.

The yt-dlp provider maps `thumbnail` and `start_time` to these fields for local
and worker downloads. Covers must be HTTP/HTTPS JPEG/PNG URLs without credentials
or uploads via `InputFile`. Thumbnails requiring headers are skipped. Other
providers may omit both fields.

Playback offsets are whole seconds, never upload dates or chapter positions.
Invalid offsets and positions at or after a known duration are omitted. Duration
is checked again before sending because ffprobe may supply it after extraction.
Offsets are also omitted when sponsor segments are removed, including ordinary
YouTube downloads with the current options, because the output timeline changes.

If Telegram rejects a send containing optional metadata, retry once without both
fields, preserving the original video arguments. Network errors are not retried
because Telegram may already have accepted the video.

API references: [Telegram sendVideo](https://core.telegram.org/bots/api#sendvideo),
[yt-dlp metadata](https://github.com/yt-dlp/yt-dlp/blob/2026.08.19/yt_dlp/extractor/common.py).
