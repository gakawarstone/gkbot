# Stream AI responses with message drafts

- STATUS: OPEN
- PRIORITY: 1

## Problem

The AI chat simulates streaming by editing a normal message every 1.5 seconds. Long responses create more messages, and failed edits can leave the FSM in its busy state. Telegram message drafts provide a native streaming path for private chats.

## Plan

1. Confirm that the configured Telegram Bot API server supports message drafts.
2. Add a private-chat streaming path based on `send_message_draft` with a stable non-zero draft ID.
3. Finalize a completed draft with a normal message.
4. Handle stopped generation when supported and cancel the upstream model stream.
5. Keep the existing edit-and-split implementation as the group-chat and compatibility fallback.
6. Coordinate chunking and failure recovery with the existing long-response task.
7. Add tests for completion, cancellation, API failure, private chat, and fallback behavior.

## Acceptance criteria

- Private AI chats stream through Telegram message drafts.
- Completion leaves one final normal response.
- User cancellation stops upstream generation and restores the FSM state.
- Groups and unsupported Bot API servers use a tested fallback.
- Streaming never leaves the user stuck in `FSM.finish`.

