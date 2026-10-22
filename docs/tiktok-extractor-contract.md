# TikTok extractor contract

`BaseExtractor.get_video_info()` constructs `InfoVideoTikTok`. Providers implement
`_extract_video_data()` and return an `ExtractedVideoData` mapping containing the
fields they obtain. The base supplies `None` for the video URL, input file and
metadata, an empty music URL, and a fresh empty image list when fields are absent.
Explicit provider values, including `None`, remain intact.

URL providers inherit `VideoUrlExtractor` and implement `_get_video_links()`.
The shared implementation selects the first link and rejects missing or empty
links. API, gallery-dl and yt-dlp providers supply their media and metadata through
`_extract_video_data()` instead.

Both public entry points translate expected extraction failures into
`SourceInfoExtractFailed`. Its `source` identifies the extractor, and `__cause__`
retains the original error. Common failures include HTTP client errors, timeouts,
and malformed response values or missing keys. A provider extends
`_expected_errors` for its service-specific exceptions. Cancellation and unexpected
errors such as `RuntimeError` propagate. The fallback continues only on
`SourceInfoExtractFailed`; exhaustion still raises `TikTokInfoExtractionFailed`.

`get_video_file_url()` remains available for existing callers. Its default
implementation returns the extracted public URL, or raises
`SourceInfoExtractFailed` when the provider has none. This also covers API
slideshows whose video URL contains audio. yt-dlp overrides the protected
`_extract_video_file_url()` hook to retain its Serveo URL behavior. Both yt-dlp
entry points retain `cleanup_delay_minutes=5`, allowing the returned file to
outlive the downloader context.

Gallery-dl and TTDownloader opt into `_normalize_url`. The shared path resolves
redirects, removes query parameters and fragments, and changes `/photo/` to
`/video/` in the resource path. It preserves the hostname and creator name.
TTDownloader applies this normalization to both public entry points.

The contract suite uses every configured entry in `_EXTRACTORS`, including both
API endpoints. Provider I/O is stubbed; these tests do not establish whether the
external provider websites are currently available. Tests cover defaults, media
and metadata, expected failures, cancellation, the compatibility method,
normalization, fallback exhaustion, malformed responses, and delayed file cleanup.
The existing TikTok service tests cover slideshow file lifetime during uploads.

```sh
make test FILE='bot/tests/services/test_tiktok_extractor_contract.py bot/tests/services/test_tiktok_service.py'
```
