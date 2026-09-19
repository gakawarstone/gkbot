# 07: Extract the FFmpeg process runner

**What to build:** Introduce one low-level component that builds and runs FFmpeg and FFprobe commands while preserving concurrency limits and subprocess failure behaviour.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] Command execution, concurrency limiting, and subprocess error propagation have one implementation.
- [ ] Existing media operations use the runner without changing their public behaviour.
- [ ] Tests cover command construction, concurrency control, and command failure.
