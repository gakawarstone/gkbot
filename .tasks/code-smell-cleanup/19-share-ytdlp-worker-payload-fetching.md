# 19: Share yt-dlp worker payload fetching

**What to build:** If the current broker contract is retained, fetch a task payload once through a shared helper and derive status and result from that payload; otherwise satisfy this outcome in the selected replacement implementation.

**Blocked by:** Existing task "Decide the YouTube worker contract".

**Status:** ready

- [ ] The selected worker architecture has one implementation for retrieving task state.
- [ ] Status polling and final result extraction do not duplicate endpoint and configuration validation logic.
- [ ] Tests cover pending, completed, malformed, and unavailable task responses.
