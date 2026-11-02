# 03: Model VK references explicitly

**What to build:** Replace the ambiguous string that may contain either a VK identifier or a short URL with an explicit domain value that can produce the final download URL.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] Parsed VK references distinguish identifiers from short URLs without string-prefix guessing by consumers.
- [ ] Supported wall, video, and shortened links retain their current behaviour.
- [ ] Tests cover valid identifiers, short URLs, full URLs, and unsupported input.
