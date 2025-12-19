# Instagram reel downloaded video not plays on ios devices

- STATUS: CLOSED
- PRIORITY: 1

you should add the convertion step to the inst reel downloaded videos using ffmpeg

## Progress
- Added `convert_video` to `FfmpegService` to convert videos to h264/aac/yuv420p for iOS compatibility.
- Integrated conversion logic into `YtdlpDownloader._download_file` for Instagram Reels.
- Created an integration test `bot/tests/handlers/test_instagram_reel.py` to verify the download and conversion process.