# Split long AI chat responses safely

- STATUS: OPEN
- PRIORITY: 2

## Problem

`AnswerHandler._stream_to_message` splits responses longer than 1500 characters only at double newlines. A single long paragraph produces an empty prefix, calls `edit_text("")`, and fails before restoring the chat state. Long code blocks and words can cause the same problem.

## Plan

1. Extract response splitting into a focused helper with a limit below Telegram's message limit.
2. Prefer paragraph and line boundaries, then split long remaining segments without producing empty chunks.
3. Preserve valid Telegram HTML when a Markdown construct crosses a chunk boundary.
4. Restore `FSM.get_message` in a `finally` block or an equivalent error path after streaming failures.
5. Add tests for long paragraphs, code blocks, exact boundaries, and streaming errors.

## Acceptance criteria

- The handler never sends or edits a message with empty text while splitting a response.
- Every emitted chunk fits the configured Telegram limit.
- Concatenating the logical chunks preserves the complete model response.
- A failed stream does not leave the user stuck in `FSM.finish`.
- Focused AI chat handler tests pass.

