# Prototype rich AI messages

- STATUS: OPEN
- PRIORITY: 2

## Problem

AI responses are converted to HTML by project code. Reasoning is rendered as a block quote, while code, lists, math, and expandable details depend on lossy Markdown conversion. Bot API 10.1 and 10.2 provide structured rich messages and rich message drafts.

## Plan

1. Build a small adapter from model response parts to rich message blocks.
2. Map reasoning to a thinking block and map code, lists, math, quotes, and details to their native block types.
3. Test nested blocks and large responses against aiogram 3.29.1 or newer.
4. Keep the current HTML renderer as a fallback for unsupported chats or servers.
5. Compare rendering, latency, and failure behavior with the existing path before enabling it by default.

## Acceptance criteria

- The prototype renders reasoning, code, lists, math, and plain text without manual HTML tags.
- Nested rich blocks do not cause excessive validation time.
- Unsupported servers and failed rich sends fall back to the current HTML path.
- Tests cover block conversion and fallback behavior.

