# 09: Extract slideshow rendering and retire FfmpegService

**What to build:** Move image and audio preparation plus slideshow rendering into a dedicated service, then remove the remaining all-purpose media facade.

**Blocked by:** 08: Move audio and video operations out of FfmpegService.

**Status:** ready

- [ ] Slideshow rendering owns its dimensions, preparation rules, and rendering options.
- [ ] TikTok slideshow creation uses the focused renderer with unchanged output behaviour.
- [ ] The old all-purpose FFmpeg service has no remaining consumers and is removed.
