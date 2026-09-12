# tiktok slideshow download fails

- STATUS: OPEN
- PRIORITY: 1

the problem is tiktok download api from ApiExtractor

```json
{
  "detail": {
    "code": 400,
    "message": "An error occurred.",
    "support": "Please contact us on Github: https://github.com/Evil0ctal/Douyin_TikTok_Download_API",
    "time": "2026-04-03 18:05:47",
    "router": "/api/hybrid/video_data",
    "params": { "url": "https://vt.tiktok.com/ZSHyubTPc/" }
  }
}
```

possible solutions

yt-dlp try to create hook that allows me to get photos urls without trying to download it as a video

local api https://github.com/Evil0ctal/Douyin_TikTok_Download_API

try to find another service that provides tt photos scraping

gallery-dl can download TikTok slideshow/photo-mode posts as separate jpg images plus the mp3 soundtrack, while yt-dlp may only expose the mp3 format for these posts.

Verified command:

```bash
uvx gallery-dl 'https://www.tiktok.com/@carharttgirll/video/7643830566579866901'
```

Possible implementation path: add a gallery-dl based fallback for TikTok slideshow downloads when yt-dlp/API extraction returns audio-only or no video URL.
