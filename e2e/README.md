# Testgram scenarios

The existing `scenarios/tiktok_video.yaml` smoke test exercises the direct
TikTok download and upload path. The exact URL from the size report is retained
in `live/tiktok_size_regression.yaml`; run it with `make e2e-live` against the
live extractor fallback chain.

TikTok marks the exact post as sensitive, so yt-dlp requires authenticated
cookies and the scenario depends on third-party fallback extractors. Testgram
does not provide HTTP/service fixtures that could make those responses
deterministic.

Testgram records the uploaded filename but discards multipart byte length and
has no `file_size_max` expectation. To make this regression fully testable in
Testgram, add deterministic HTTP fixtures and record uploaded file sizes with a
maximum-size assertion. Its fake server's 50 MiB request limit still catches the
original 83 MiB upload, while local tests enforce the 15 MiB compression policy,
compact format selection, and no-op behavior for already-small TikTok files.
