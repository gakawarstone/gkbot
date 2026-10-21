# 08: Move audio and video operations out of FfmpegService

**What to build:** Move voice conversion, video conversion, and video metadata reading into focused services backed by the shared process runner.

**Blocked by:** 07: Extract the FFmpeg process runner.

**Status:** ready

- [ ] Voice conversion, video conversion, and metadata reading have separate public contracts.
- [ ] Current callers use the focused services and retain their existing results and error behaviour.
- [ ] Focused unit tests cover each operation without invoking unrelated slideshow logic.
