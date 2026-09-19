# 04: Centralize yt-dlp source detection

**What to build:** Classify supported download URLs once and use the result for option selection, metadata retrieval, downloading, and post-processing.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] YouTube, Shorts, TikTok, Instagram, regular VK, and VK clips are classified by one component.
- [ ] Downloader and options code no longer maintain independent regular expressions or prefix cascades for the same sources.
- [ ] Tests cover representative URL variants and unknown sources.
