# 12: Migrate specialized feed processors

**What to build:** Move media-specific feed sources and their keyboard integrations into independent registry entries while preserving source-specific callbacks.

**Blocked by:** 10: Add a feed processor registry.

**Status:** ready

- [ ] Specialized video, audio, gallery, and download-button sources use registry entries.
- [ ] Existing keyboard payloads and callback behaviour remain compatible.
- [ ] Source-specific failures still fall back to the generic feed-item response.
