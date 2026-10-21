# Clean up temporary media on every exit path

- STATUS: OPEN
- PRIORITY: 1

## Problem

`HttpService.download_file` returns a path inside a new cache directory without returning ownership of that directory. The download handler sends the file but never deletes it. FFmpeg conversion methods also delete their cache directories only after successful conversion and reads, so failures leave files behind.

## Plan

1. Give downloaded files an explicit ownership model, such as an async context manager that cleans its cache directory.
2. Update the document download handler to keep the file alive through Telegram upload and then delete it.
3. Put FFmpeg cache cleanup in `finally` blocks.
4. Make cleanup tolerate an already-removed directory without hiding the original error.
5. Add success and failure-path tests that assert temporary directories are removed.

## Acceptance criteria

- Document downloads leave no cache directory after sending or failing.
- FFmpeg conversions clean their work directories after success and failure.
- Tests verify cleanup without relying on process exit.

