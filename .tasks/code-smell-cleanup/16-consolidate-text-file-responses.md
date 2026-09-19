# 16: Consolidate generated text-file responses

**What to build:** Give file-processing handlers one reusable way to turn text lines into a Telegram document response.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] Test conversion and source sorting use the same text-document response helper.
- [ ] File names, line order, encoding, and Telegram response behaviour remain unchanged.
- [ ] Tests cover empty, single-line, and multi-line documents.
