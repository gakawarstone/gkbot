# AI chat streaming

Private chats use Telegram drafts with one non-zero ID per response. On
completion, responses up to 4096 UTF-16 units become one normal message; longer
responses are split safely. History keeps the original Markdown. Groups and
servers rejecting drafts use the existing edit-and-split fallback. On a draft
failure, fallback continues the same model stream with the text already received;
`RetryAfter` cooldowns are respected.

Native stop requires Bot API 10.3. A matching stop update cancels the model
stream and closes its HTTP response and client. FSM recovery also runs after
errors and preserves a concurrent `/exit`. Stop updates have no `from_user`:
`active_generations` identifies a task by bot, chat, topic and draft ID. Its
published `ActiveGeneration` fields are `task`, source `state` and `stopped`.

The configured server image is pinned to Bot API 10.3. Older servers may accept
drafts but ignore stop parameters. See [server verification and rollout](../services/bot-api/README.md).
Drafts expire after 30 seconds without an update, so a stalled model can lose its
preview. No deployment or live Telegram checks were performed for this change.

## Contracts for dependent work

- `_stream_to_draft(stream, draft_id) -> str` sends the draft and final response,
  returning the original Markdown. The caller closes the generator.
- `_private_response(stream) -> str | None` registers cancellation; `None`
  means the user stopped generation.
- `_send_draft(draft_id, html) -> bool` preserves the source topic and returns
  `False` on Telegram API failure after any cooldown.
- `_stream_to_message(message, stream) -> str` remains the fallback. Optional
  `text` and `reason` keyword arguments carry the already received content.
- `_answer(text, **kwargs) -> Message` and fallback chunks preserve the source
  `message_thread_id`, including without `is_topic_message=True`.
- `split_response(markdown, limit)` and the shared renderer retain the
  prerequisite's API. Rich rendering and global topic/FSM isolation are separate.

Telegram API: [sendMessageDraft](https://core.telegram.org/bots/api#sendmessagedraft),
[MessageGenerationStopped](https://core.telegram.org/bots/api#messagegenerationstopped).
