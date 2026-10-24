# AI chat streaming

Private AI chats use `sendMessageDraft` with a random, non-zero ID that stays
fixed for the response. The first draft says "Подождите". Updates are sent at
most once every 1.5 seconds as model chunks arrive. Drafts are temporary; the
completed response is persisted with `sendMessage`.

The draft shows the latest rendered part, up to 4096 UTF-16 units. A completed
response that fits this limit produces one normal message. Longer responses
use the existing safe HTML splitter at 4096 units and send all parts in order.
The complete, original Markdown is retained in conversation history. Empty or
reasoning-only output produces "Модель не вернула ответ.".

Groups retain the existing edit-and-split implementation at 1500 units. A
Telegram API error while sending a draft switches that generation to this same
fallback. Already received content is replayed locally, then the original model
stream continues. It does not issue another model request. A `RetryAfter`
cooldown is observed before sending the fallback message. Normal final-message
failures propagate to the existing error handler without retrying the final
response and risking duplicates.

## Stop and cleanup

On Bot API 10.3, drafts request `can_stop=True` and `keep_on_stop=False`. A
`stopped_message_generation` update cancels the matching generation task. The
bot closes the upstream OpenRouter HTTP stream and client, sends
"Генерация остановлена.", and restores the source FSM to `get_message`. It does
not add an incomplete model answer to history. The user's submitted prompt
remains in history, as it does after a failed response.

Stop updates have `chat`, `draft_id`, and optional `message_thread_id`; they have
no `from_user`. `chatgpt._generation.active_generations` maps
`(bot_id, chat_id, message_thread_id, draft_id)` to the running task and saved
source `FSMContext`. The observer needs no injected user or FSM context.
Duplicate, unknown, completed, wrong-bot, and wrong-topic stops are ignored.
Entries are removed on success, failure, and cancellation. External task
cancellation propagates after cleanup. FSM recovery runs in `finally`, including
when sending the stop status fails; it preserves a concurrent `/exit` state
change.

The model generator is explicitly closed on every exit from the handler.
`OpenRouter.stream` owns its SDK client and HTTP completion stream through async
context managers, so cancellation closes the connection even when the generator
is suspended at a yielded token.

## Server compatibility

The configured Compose image is pinned to Bot API 10.3 by the aiogram upgrade.
On 2026-10-23, read-only inspection found that the running `gkbot-api` still used
image ID `sha256:5518232e8ede9b6de8dfc8a665a03104005732eb5d0ce33c5161ca6a361c8e77`.
An isolated `--version` invocation with no network or volumes reported Bot API
9.5. The pinned image reported Bot API 10.3. Neither production configuration nor
running containers were changed.

The first draft request probes support for that chat and configured API server
on each generation. Servers that reject drafts use the message fallback. Older
servers can accept drafts while ignoring unknown stop-control parameters; a
successful draft request does not establish stop-button support. Deploy the
pinned 10.3 server to enable native stop controls. There is no server version
endpoint used or assumption that merging Compose updates a running server.
See [server rollout instructions](../services/bot-api/README.md).

Drafts expire after 30 seconds without an update, or when a normal message
arrives. Updates are driven by incoming model chunks. A model that stalls for
longer can therefore lose its visible preview before generation finishes.

## Contracts for dependent work

- `AnswerHandler._stream_to_draft(stream, draft_id) -> str` streams and persists
  the response, returning the full original Markdown. It owns draft transport
  and compatibility fallback; the caller owns generator closure.
- `_private_response(stream) -> str | None` registers cancellation and returns
  `None` for a user-stopped response.
- `_send_draft(draft_id, html) -> bool` preserves the source topic, requests stop
  controls, and returns `False` after a Telegram API error and any cooldown.
- `_stream_to_message(message, stream) -> str` retains the prerequisite's group
  and compatibility fallback contract.
- `_answer(text, **kwargs) -> Message` explicitly copies the source
  `message_thread_id`, including when `is_topic_message` is absent or false.
  Additional fallback messages copy the same source topic. Editing is addressed
  by the response message ID.
- `split_response(markdown, limit)` and the shared Markdown renderer remain the
  prerequisite's API. Draft previews and final messages use HTML. Rich message
  rendering and application-wide topic/FSM isolation belong to dependent work.

## Verification

Tests use real aiogram request objects and dispatcher routing with a recording
session. They cover private drafts, stable IDs, HTML and Unicode bounds, a single
final message below the Telegram limit, long responses, groups, old-server and
mid-stream failures, reasoning-only answers, and native/external cancellation.
Stop tests exercise both blocked model reads and suspended generators while a
draft is being sent, including failure of the stop status. HTTP stream tests use
the installed OpenAI SDK with a local mock transport and check that both the
response body and client close.

```bash
make test FILE='bot/tests/handlers/test_chatgpt_drafts.py bot/tests/handlers/test_chatgpt_answer.py bot/tests/services/test_openrouter_stream.py'
make test
make lint FILE='bot/handlers/user/chatgpt/answer.py bot/handlers/user/chatgpt/_generation.py bot/handlers/user/chatgpt/__init__.py bot/services/llm/openrouter.py bot/tests/handlers/test_chatgpt_drafts.py bot/tests/handlers/test_chatgpt_answer.py bot/tests/services/test_openrouter_stream.py'
```

Live Telegram checks were not run. No bot token, root checkout `.env`, or
production network requests were used.

## Official API references

- [Telegram sendMessageDraft](https://core.telegram.org/bots/api#sendmessagedraft)
- [Telegram MessageGenerationStopped](https://core.telegram.org/bots/api#messagegenerationstopped)
- [aiogram send_message_draft](https://docs.aiogram.dev/en/latest/api/methods/send_message_draft.html)
- [aiogram stop update](https://docs.aiogram.dev/en/latest/api/types/message_generation_stopped.html)
- [OpenAI SDK stream cleanup](https://github.com/openai/openai-python/blob/v2.26.0/src/openai/_streaming.py)

Results after test review on 2026-10-24: 68 focused tests passed; the full suite
passed with 190 passed and 13 skipped. Scoped `make lint` for the three reviewed
test files passed Ruff, typos, mypy, and pyright. The review changed no production
code or prerequisite tests.
