# Private AI topics

Proposal only. `/topic` is not enabled and the task remains OPEN. Runtime
integration is blocked on explicit owner approval of context-design
[PR #29](https://github.com/gakawarstone/gkbot/pull/29); its documentation is not
an implemented runtime dependency. This review does not grant that approval.

## User behavior

`/topic <name>` creates a private topic, using `AI-чат` when no name is supplied.
Reject names longer than 128 characters without entering another FSM step.
Send the new topic a welcome explaining `/chat` and `/exit`. `/chat` starts or
restarts AI history only in that topic; `/exit` ends only that topic's flow.
Creating a topic leaves the source conversation unchanged. Users select existing
topics through Telegram, without an application-level selected-topic pointer.
User-created topics use the same `/chat` entrypoint; plain text does not enable AI.

Register `/topic` before state-specific text handlers so it cannot become an AI
prompt. Advertise it only when isolation and rejection paths are implemented.
The ordinary private conversation remains a separate session. Telegram topics
can outlive their in-memory histories, which expire or disappear on restart.

## Support and failures

Private topics require BotFather topic mode. `getMe.has_topics_enabled` checks
bot capability; `allows_users_to_create_topics` describes user creation rights,
not the bot command's permission. `createForumTopic` supports private chats and
names of 1 to 128 characters. See the official
[private topics guide](https://core.telegram.org/bots/features#topics-in-private-chats),
[capability fields](https://core.telegram.org/bots/api#user), and
[creation method](https://core.telegram.org/bots/api#createforumtopic).

Accept only ordinary private bot chats. Unsupported chat types, business chats,
and absent topic capability receive a clear explanation and `/chat` alternative
without changing state/history. Channel `direct_messages_topic_id` is a separate
mechanism and is outside this command's scope.

Handle concrete Telegram errors: distinguish unsupported/inaccessible requests
from transient failures. Do not automatically retry ambiguous creation failures,
which could create duplicates. If creation succeeds but the welcome fails, report
that the topic exists and `/chat` can be sent there; do not create it again.
Creation itself does not enter AI FSM state. No live capability check, BotFather
change, or deployment has been performed. Server rollout belongs to the
[existing operator procedure](../services/bot-api/README.md).

## Session isolation and routing

Use `FSMStrategy.USER_IN_TOPIC` and the resolved `FSMContext.key` for middleware
storage, covering bot/chat/user/thread and the existing business/destiny fields.
An unthreaded chat uses `thread_id=None`. Callbacks use their source message's
topic and callback sender. Missing/inaccessible topic context must not select
another conversation. See [aiogram's strategy contract](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/strategy.html).

Change both acquire and release keys in the existing bounded `UserDataStore`.
Use one store for messages/callbacks, with each topic counting toward its capacity;
do not add another topic mapping. Preserve typed `UserData`, its required
`delete_queue: []`, and the injected `data["data"]` boundary. Context managers
consume that mapping and do not construct session identity.

Preserve retention's pins through the handler and final FSM lookup, deferred
cleanup, and expired-session reset before a selected handler can use missing
history. AI's temporary `finish` during generation is not session completion.
Serialize overlapping updates within one session while allowing different topics
to progress. Stop updates must cancel without waiting on the generation's lock.

Carry the source `message_thread_id` through replies, validation, status/actions,
drafts, split/fallback messages, and user-facing errors. Explicit routing is
needed where `Message.answer()` would drop a thread without `is_topic_message`.
The creation welcome targets the new topic. Edits retain their message identity;
a deleted topic must not trigger fallback to the unthreaded chat. Administrator
traceback delivery remains separate from the user-facing error.

## Dependencies to reuse

- Streaming [PR #39](https://github.com/gakawarstone/gkbot/pull/39), reviewed head
  `d069c1f50b39584444dd71a5cbb2f0edc2e933c2`, retains source-topic sends and a
  cancellation registry keyed by `(bot_id, chat_id, message_thread_id, draft_id)`.
  Stop updates have no `from_user`; use the saved source context. Preserve
  `_private_response(stream) -> str | None`, where `None` means stopped, and the
  existing draft/send helpers. Fallback remains
  `_stream_to_message(message, stream, *, text='', reason='')`, also callable
  with two arguments. Continue the same model stream; the source handler owns
  `aclosing`. Preserve raw history, safe splitting, and concurrent `/exit` state.
  Native stop requires server 10.3; stalled drafts can expire after 30 seconds.
  Splitter prerequisite [#20](https://github.com/gakawarstone/gkbot/pull/20) is
  merged; #39 still targets its parent branch. Do not rebuild that stack here.
- Retention [PR #37](https://github.com/gakawarstone/gkbot/pull/37), reviewed head
  `b4a1a4684e257dca6fed98fb6813c49d6c046de3`, already integrates typing
  [#40](https://github.com/gakawarstone/gkbot/pull/40). Use the whole head rather
  than `dd6264c` alone. `acquire(key)` needs a matching
  `release(key, entry, session_active=final_status)` in `finally`. Keep the
  published TTL/capacity/cleanup and typed handler contracts; do not repeat them.
- Context design [#29](https://github.com/gakawarstone/gkbot/pull/29), reviewed
  head `7baef250f81a6b4a335e4aa7ac52009777a714af`, proposes explicit field keys
  while retaining typed `ctx` and the mutable mapping. The simplified validation
  policy and identity guarantees remain subject to owner approval. Do not
  implement the replacement or treat its documentation commit as runtime code.

After the required decision, integrate published commit sets in this worktree
with a PR base excluding prerequisite diff. Do not duplicate their implementations
or merge their PRs automatically.

## Acceptance checks still required

- Through the real dispatcher/middleware, run two simultaneous topics for one
  user plus an unthreaded chat. Verify distinct FSM/history/queue objects and
  callbacks; include other users/chats/bots and unavailable callback context.
- Restart, exit, expire, or cancel topic A while B streams. Only A may change.
  Exercise capacity pressure, pins, cleanup, and the existing typed-data tests.
- Record real outgoing methods for welcome, replies, status/actions, drafts,
  long splits, fallback, and errors. Verify source threads even when response
  metadata lacks the topic flag; avoid mocks that discard routing metadata.
- Test `/topic` during AI mode, default/Unicode/overlong names, user-created
  topics, unsupported chats/capabilities, API/network failures, and welcome
  failure. Assert clear responses, unchanged source state, and no partial flow,
  duplicate creation, or cross-topic fallback.

Run existing relevant regressions and scoped static checks with the implementation.
The previous offline aiogram probe confirmed topic-key/answer/callback behavior;
it does not satisfy these application criteria. Keep the task file until they pass.
