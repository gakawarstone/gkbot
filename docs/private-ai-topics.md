# Private AI topics

Status: implementation proposal, blocked on prerequisite results. This document
does not enable `/topic`. The task remains open until the application tests below
pass against the integrated implementation.

## User behavior

`/topic <name>` creates a new private topic for a separate conversation. With no
name, use `AI-чат`. Reject a supplied name longer than 128 characters before
calling Telegram. Do not collect the name through another FSM step.

Send the new topic a welcome message explaining `/chat` and `/exit`. Opening the
topic and sending `/chat` starts an empty AI history there, using the existing AI
chat initialization. Creating a topic does not reset, copy, or switch the source
conversation. Users select existing conversations through Telegram's topic list.
There is no application-level selected-topic pointer.

Topics created directly in Telegram behave the same way: `/chat` starts AI mode
in that topic. Plain text in a topic does not automatically enable AI mode.
`/chat` restarts only that topic's AI history; `/exit` exits only that topic's flow.
The ordinary private conversation remains a separate session. A Telegram topic
can outlive its in-memory AI history, which follows the retention policy and is
lost when the process restarts.

Register `/topic` before handlers that consume state-specific text, including the
AI prompt handler. Otherwise a command sent during AI mode could reach the model.
Add the command to both the user command registry and the advertised command list
only when the implementation and rejection paths are ready.

## Confirmed Telegram capabilities

Private topics require enabling the bot's topic mode in BotFather. Users can also
organize conversations into topics when allowed by the bot configuration.
[Telegram's private topics guide](https://core.telegram.org/bots/features#topics-in-private-chats).

`getMe` exposes `has_topics_enabled` and `allows_users_to_create_topics`.
`createForumTopic` supports private chats and accepts names of 1 to 128 characters.
The user-creation flag describes the user's ability to create/delete topics; it
is not a requirement for the bot's create command.
[User capabilities](https://core.telegram.org/bots/api#user),
[createForumTopic](https://core.telegram.org/bots/api#createforumtopic).

Use `message_thread_id` for these conversations. Channel direct messages use a
different mechanism, `direct_messages_topic_id`, and are outside this command's
scope. Sending text, drafts, and chat actions accepts `message_thread_id`.
[Message](https://core.telegram.org/bots/api#message),
[sendMessage](https://core.telegram.org/bots/api#sendmessage),
[sendMessageDraft](https://core.telegram.org/bots/api#sendmessagedraft),
[sendChatAction](https://core.telegram.org/bots/api#sendchataction).

The deployed bot's topic setting has not been checked or changed. Do not read
the root checkout's `.env`, enable BotFather settings, or deploy as part of this
change. The configured server requirement and separate rollout procedure remain
in [Bot API compatibility](../services/bot-api/README.md).

## Reject unsupported requests before changing state

Accept `/topic` only in an ordinary private chat with the bot. Groups, forum
supergroups, channels, channel direct messages, and business connections receive
a clear explanation that this command creates topics in a private bot chat.
Do not create a group forum topic as a fallback.

Check the bot's topic capability before creation. If unavailable, respond:
`Темы в личном чате сейчас недоступны. Используй /chat для обычного AI-чата.`
An absent capability flag is not proof of support. Older servers can reject the
method even if the client exposes it. Handle the creation request's concrete
Telegram exceptions without treating every network error as unsupported topics.
For a transient failure, ask the user to retry. For a rejected or inaccessible
request, explain that the topic could not be created. Keep all existing session
state and history unchanged in either case.

Topic creation itself does not enter AI FSM state. If creation succeeds but the
welcome message fails, leave the topic available, report that it was created
but could not be initialized, and explain that `/chat` can be sent inside it.
Do not automatically retry creation after an ambiguous transport failure, which
could create duplicate topics.

## FSM and middleware storage

Configure the dispatcher with `FSMStrategy.USER_IN_TOPIC`. It separates state by
user, chat, and topic, unlike the current default `USER_IN_CHAT`, which drops the
topic from the key.
[aiogram FSM strategies](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/strategy.html).

Use the resolved `FSMContext.key` as the middleware store key. `StorageKey`
includes bot, chat, user, thread, business connection, and destiny, avoiding a
second hand-written key algorithm. The retention store will accept a `Hashable`
key. Every topic counts toward the same store capacity; do not introduce a second
unbounded topic-to-context mapping. Both message and callback middleware must
use the same store instance and the same resolved key.

An unthreaded chat uses `thread_id=None`. Callback queries use the original
message's topic and the callback sender, rather than the original message's bot
sender. For inline callbacks or inaccessible messages without a resolvable topic,
do not substitute a known topic or load another conversation's history.

The existing context manager reads `data["data"]`. It can continue doing so after
the dictionary is scoped to the resolved FSM key. Apply the approved context
manager design when available; do not implement its replacement here. AI history,
delete queues, temporary flow properties, and cached timezone data all become
scoped to that same session dictionary. The database remains the source of truth
for user settings.

Preserve the published middleware typing contract from PR #40 when changing
mapping ownership. The outer `MiddlewareData` extends aiogram's injection data;
its `data` and `admins` fields are optional before injection. The nested mapping
is `UserData`, with a required `delete_queue: list[Message]`, optional flow fields,
and nullable `tz`. New session entries must start with `{"delete_queue": []}`,
including entries first acquired by a callback. Keep `require_user_data` and the
typed class/function handler boundaries. A topic-key migration must not replace
these types with unrestricted dictionaries or confuse the outer context with
the injected session data.

Use event isolation keyed by the FSM storage key so overlapping updates in one
topic cannot mutate the same history or reset a running generation. Different
topics must be able to progress concurrently. A draft stop event must be able to
cancel a running generation without waiting for its message-handler lock.

Expiry must not leave `FSM.get_message` pointing to missing history. Integrate
the prerequisite's expired-session reset behavior and require a new `/chat`
where necessary. `FSM.finish` is the current AI busy state during generation,
not evidence that a conversation is complete. Evaluate retention after the
handler's final state restoration, while preserving its active pin.

Storage remains in memory. A restart starts new FSM and middleware storage
together. No persistent database migration or import of other worktrees' live
session objects is needed.

## Replies, progress, and cancellation

Use the source topic throughout initialization, AI replies, fallback splitting,
status messages, command validation, and user-visible errors. A welcome message
after creation targets the new topic explicitly, rather than using the source
command's `answer()` shortcut.

The installed aiogram 3.31.0 `Message.answer()` includes the thread only when
`is_topic_message` is true. Split responses must not rely on a test double or an
API response silently preserving that flag. Carry the source topic explicitly
through the streaming implementation, including subsequent split messages.
Existing media status actions in `handlers/text/{tiktok,instagram,ytdlp_short}.py`
also need the originating `message_thread_id` because these handlers can receive
messages after the user exits AI mode inside a topic.

Edits address an existing message by its chat and message ID. New sends, drafts,
and chat actions must use the source thread. If the topic disappears during a
generation, fail within that conversation and restore/clear its own state. Do
not retry the reply in the unthreaded private chat.

The installed `MessageGenerationStopped` has `chat`, `draft_id`, and
`message_thread_id`, but no `from_user`. With `USER_IN_TOPIC`, aiogram therefore
does not automatically resolve its user-scoped FSM context. The published drafts
implementation retains the source context with the active generation and cancels
by bot/chat/thread/draft identity. Integration tests must verify that a stop in
topic A cannot cancel or restore the state of topic B.

User-facing AI failures go to the source topic. Existing traceback delivery to
administrator chats stays an operational notification, independent of the
user-facing response.

## Prerequisites and integration order

aiogram upgrade [PR #11](https://github.com/gakawarstone/gkbot/pull/11) is already
merged into this worktree's base `fc19464`. Do not reapply it.

Prerequisite status as reported on 2026-10-23:

- Draft streaming, thread `mcp:4bc598c3-6de2-4025-8740-daf05aaaaae7`, branch
  `task-20261023-stream-ai-with-message-drafts`, published ready/open
  [PR #39](https://github.com/gakawarstone/gkbot/pull/39), implementation/head
  commit `e24bebba1d1b697768cd72f0496472a63427e7d2`. Approval and merge remain
  pending. It is stacked on branch `task-20261022-split-long-ai-chat-responses`,
  [PR #20](https://github.com/gakawarstone/gkbot/pull/20), head
  `6c734b1b4d7ee7d49313c8a6b0cc870c6ec0848d`, integrated by an ordinary merge.
  Preserve both prerequisite commit sets when choosing the integration base.
  The author reports 78 focused tests and 200 full-suite tests passed, with 13
  skipped. Ruff, typos, and pyright pass for the changed files; targeted mypy
  stops at the existing imported `generate_image.py:43` error.
- Bounded retention, thread `mcp:45f94e95-1569-4cd9-9f99-6fc68dc05eb8`, branch
  `task-20261022-bound-middleware-user-data-retention`, published ready/open
  [PR #37](https://github.com/gakawarstone/gkbot/pull/37), final head
  `b4a1a4684e257dca6fed98fb6813c49d6c046de3`. Approval and merge are pending.
  It is stacked on typing #40 at `1813b3e9079a70b4a086193fc8a0cfc87e757a36`.
  Use the entire published head, not the pre-integration `dd6264c` alone. Its
  source thread, `docs/user-data-retention.md`, and store/middleware code have
  been read. The author reports 61 middleware tests and 164 full-suite tests
  passed, with 13 skipped, and all four scoped lint tools passing.
  The instance-owned `UserDataStore` accepts `Hashable` keys, defaults to 4096
  entries and 3600 seconds idle TTL, pins active handlers, and initializes typed
  `UserData` with the required queue. Each successful acquire must have a matching
  release in `finally`, after final FSM lookup. Expiry/cleanup defer deletion of
  pinned dictionaries. Completed flows retain only a nonempty deletion queue;
  missing context with a nonterminal FSM clears that FSM and skips the selected
  handler after explaining the restart. One middleware/store serves messages and
  callbacks and closes on dispatcher shutdown. This task owns changing its
  initial user-ID key consistently in both acquire and release, using the same
  bounded store with no auxiliary mapping.
- Context design, thread `mcp:566c7237-8a29-4c77-84c0-7f2700fa9a76`, branch
  `task-20261022-replace-handler-context-manager`, published documentation-only
  [PR #29](https://github.com/gakawarstone/gkbot/pull/29), commit
  `6451efa9c5360ff84fdac212f82e911826eec185`. The PR is open and the design
  awaits explicit owner approval. Its proposed contract keeps `BaseContextManager`,
  `props`, typed `ctx`, the injected mutable `data["data"]` mapping, flat keys,
  and live `Message` identity. Writes become `set("field", value)` and cleanup
  uses `clean_context(*preserve: str)`, with recursive list/dict/union validation
  without coercion. The manager does not choose session identity. This is a
  proposed interface, not an approved or implemented runtime prerequisite.
  Do not import the documentation commit as a substitute for implementation or
  preempt the owner's decision.

All three authors have this downstream thread ID,
`mcp:93bebd65-7048-4378-84db-871a65c8e253`, and were asked to send their published
result. Draft streaming and final retention results have now been read. Explicit
owner approval of the context design remains outstanding in the source thread;
neither documentation PR publication nor these other ready results replaces that
decision. Resume runtime integration after the decision is recorded. Use published
commits only,
resolve any integration conflicts in this worktree, and select a stacked PR base
that does not duplicate prerequisite changes. Do not merge those PRs automatically.

The streaming contract to reuse is `_stream_to_draft(stream, draft_id) -> str`,
`_send_draft(draft_id, html) -> bool`, and `_private_response(stream) -> str | None`,
where `None` means the user stopped generation. Its registry key is
`(bot_id, chat_id, message_thread_id, draft_id)`; stop routing does not require
`from_user` or injected FSM state. `_answer` and new fallback chunks explicitly
preserve the source topic. Draft errors replay accumulated content/reason into
the existing edit/split fallback without another model request. Groups use the
1500-unit fallback; successful draft responses finalize as safe HTML chunks of
4096 UTF-16 units while retaining the full raw Markdown history. FSM recovery
does not undo a concurrent `/exit`. Global topic FSM/middleware isolation remains
this task's work. Reuse these paths rather than implementing another streamer.

The author verified the running server image as Bot API 9.5 and the pinned binary
as 10.3 without deployment. Native stop controls require server rollout to 10.3;
draft acceptance alone does not prove stop-control support. Draft previews can
expire if the model stalls for more than 30 seconds. These reported limitations
must remain visible in the integrated documentation.

The related middleware typing result is ready/open
[PR #40](https://github.com/gakawarstone/gkbot/pull/40), base `dev-3.0`, branch
`task-20261023-type-aiogram-middleware-data`, commit
`1813b3e9079a70b4a086193fc8a0cfc87e757a36`. Approval and merge are pending. Its
source thread `mcp:b95416bd-21c7-4fca-beff-5b0c940d7960` and published
`docs/middleware-data.md` have been read. It keeps the shared user-ID cache and
does not implement eviction, retention, or topic isolation. Retention's final
head already integrates its published types and consumer updates; do not apply
the typing commit a second time or repeat its migration here. The author
reports 134 passed, 13 skipped and all four scoped lint tools passing for 21 files.

## Required application tests

These are implementation acceptance tests to add after the prerequisites land;
the offline library probe below does not satisfy them.

1. Feed `/chat` updates for one user in topics A and B through the real dispatcher
   and middleware. Assert different FSM and history objects. Hold the model
   stream in A, complete a prompt in B, then finish A. Each history contains only
   its own prompt/reply and each flow returns to `get_message`.
2. Include an unthreaded private conversation, a second user, another chat, and
   another bot. Assert no context collisions. Feed callbacks from A and B and
   assert they use their respective message contexts. Inaccessible/inline
   callbacks must not load another topic's data.
3. Restart `/chat` and run `/exit` in A. Assert B's history, delete queue, active
   generation, and state survive unchanged. Exercise TTL expiry, entry pressure,
   active pins, and topic-local cleanup using the retention store's contract.
   Verify every fresh message/callback session has the required typed deletion
   queue and rerun the middleware runtime/static contract tests from PR #40.
4. Record actual outgoing method objects with a fake Bot session. Assert the
   source thread on welcome, prompt validation, status, draft updates, final
   response, long-response splits, compatibility fallback, and errors. Do not use
   the existing `MockedMessage.answer`, which drops topic metadata.
5. Stop generation in A using a real `MessageGenerationStopped` update while B
   streams. Assert only A's upstream generator closes and only A's FSM recovers.
   Include matching draft IDs across different chats/topics to expose registry
   keys that omit chat or thread identity.
6. Test `/topic` before and during AI mode, default/Unicode/overlong names, and
   creating a second topic without changing source history. Verify `/chat` works
   in bot-created and user-created topics.
7. Reject unsupported chat types, disabled/missing topic capability, API method
   rejection, inaccessible chat, network failure, and welcome-send failure. Assert
   a clear response, no new partial FSM flow, no source-state mutation, and no
   automatic duplicate creation or cross-topic fallback.
8. Run focused tests/static checks for every changed file, then the full suite.
   Record pre-existing unrelated lint failures separately.

After unit verification, an operator can enable topics on a controlled test bot
and exercise two private topics with concurrent AI prompts, cancellation, and
`/exit`. This has not been performed with live Telegram credentials.

## Evidence from this worktree

Prepared against `fc19464` on 2026-10-23 using `uv sync --all-extras`, without
accessing production credentials or modifying a running server.

- The installed wheel is aiogram 3.31.0. It exposes `USER_IN_TOPIC`, topic
  capability fields, and the expected message/draft/action thread parameters.
- An offline probe constructed real private `Message` and `CallbackQuery`
  objects for thread IDs 11, 22, and `None`, resolved them through aiogram's
  `UserContextMiddleware` and `FSMContextMiddleware`, and wrote distinct states
  into `MemoryStorage`. All states remained distinct; clearing thread 11 left
  thread 22 unchanged. `Message.answer()` preserved each source thread. The
  probe used `is_topic_message=True` for topic messages and made no HTTP requests.
- Baseline `make test`: **122 passed, 13 skipped**.
- Baseline `make lint`: **383 existing Ruff findings**, stopping before the other
  stages. No runtime files were changed for this proposal.

The `/topic` implementation, middleware migration, application acceptance tests,
and task-file removal remain pending. This proposal is not a completed feature.
