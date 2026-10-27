# AI chat streaming

Private AI chats stream through `sendMessageDraft` with one non-zero ID per
response. The first draft says "Подождите". Updates show the latest rendered part,
up to 4096 UTF-16 units, at most once every 1.5 seconds as model chunks arrive.
Completion sends one normal message if it fits that limit; longer responses use
the existing safe HTML splitter and send all parts in order. Conversation history
retains the complete original Markdown. Empty or reasoning-only output produces
"Модель не вернула ответ.".

Groups use the existing edit-and-split implementation at 1500 units. A Telegram
API error while sending a draft switches to the same fallback with the text and
reasoning already received. The original model stream continues without another
model request. `RetryAfter` cooldowns are observed. Normal final-message failures
propagate to the existing error handler without retrying a possibly delivered
response.

## Stop and cleanup

Drafts request `can_stop=True` and `keep_on_stop=False`. A matching
`stopped_message_generation` update cancels generation, closes the upstream
OpenRouter HTTP stream and client, and sends "Генерация остановлена.". An
incomplete model answer is not added to history; the submitted prompt remains.

Stop updates have no `from_user` or injected FSM context. The cancellation
registry uses `(bot_id, chat_id, message_thread_id, draft_id)` to find the running
task. `ActiveGeneration` retains its published `task`, source `state`, and
`stopped` fields. Duplicate, stale, wrong-bot and wrong-topic stops are ignored;
entries are removed on every exit. The source handler restores `get_message` in
`finally`, including when the stop status fails, while preserving a concurrent
`/exit`. External task cancellation propagates after cleanup.

The source handler owns generator closure through `aclosing`. `OpenRouter.stream`
uses async context managers for its client and HTTP completion stream, including
when cancellation happens while suspended at a yielded token.

## Compatibility and limits

The configured server image is pinned to Bot API 10.3. Each generation probes
draft support with its first request. Servers rejecting drafts use fallback;
older servers accepting drafts may ignore stop parameters. Native stop controls
require 10.3. See [server verification and rollout](../services/bot-api/README.md).
No deployment or live Telegram checks were performed for this change.

Drafts expire after 30 seconds without an update, or when a normal message
arrives. Updates follow incoming model chunks, so a stalled model can lose its
visible preview before completion.

## Contracts for dependent work

- `_stream_to_draft(stream, draft_id) -> str` handles drafts, persistence and
  compatibility fallback, returning the original Markdown. The caller owns
  generator closure.
- `_private_response(stream) -> str | None` registers cancellation and returns
  `None` when the user stops generation.
- `_send_draft(draft_id, html) -> bool` preserves the source topic, requests stop
  controls, and returns `False` after a Telegram API error and any cooldown.
- `_stream_to_message(message, stream) -> str` remains the group/fallback entry
  point. Optional keyword arguments `text` and `reason` carry already received
  content when switching from drafts.
- `_answer(text, **kwargs) -> Message` and new fallback chunks explicitly preserve
  the source `message_thread_id`, including without `is_topic_message=True`.
- `split_response(markdown, limit)` and the shared Markdown renderer retain the
  prerequisite's API. Rich rendering and global topic/FSM isolation belong to
  dependent work.

API references: [sendMessageDraft](https://core.telegram.org/bots/api#sendmessagedraft),
[MessageGenerationStopped](https://core.telegram.org/bots/api#messagegenerationstopped).
