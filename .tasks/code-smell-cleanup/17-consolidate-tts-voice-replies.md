# 17: Consolidate TTS voice replies

**What to build:** Share text-to-speech conversion and voice-message delivery between direct text handling and the interactive FSM flow.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] Both entry points use one conversion-and-reply operation.
- [ ] FSM transitions remain outside the shared operation.
- [ ] Provider choice, input validation, and voice output remain covered by tests.
