# Private AI topics

`/topic <name>` creates a topic in an ordinary private bot chat. The default name
is `AI-чат`; names longer than 128 characters are rejected without starting a flow.
Open the new topic and send `/chat` to start its AI conversation. Users select
existing topics through Telegram's topic list. User-created topics work the same
way. Creating a topic does not reset or switch the source conversation.

`/chat` restarts history only in the current topic. `/exit` ends only that topic's
flow. The unthreaded conversation is a separate session. Histories remain in
memory, subject to [retention](user-data-retention.md), and disappear on restart.

## Availability and errors

Enable private topic mode through BotFather. The command checks
`getMe.has_topics_enabled`; user topic-creation permissions do not gate the bot's
command. Groups, channel direct messages, business chats, and bots without topic
mode receive an explanation and a `/chat` alternative without changing FSM state.
See Telegram's [private topics guide](https://core.telegram.org/bots/features#topics-in-private-chats)
and [creation API](https://core.telegram.org/bots/api#createforumtopic).

Creation is never retried automatically: a transport failure may hide a created
topic. Check the topic list before trying again. If only the welcome fails, the
bot reports that the topic exists and `/chat` can be sent there. Creation does not
start AI mode or allocate another topic-to-session registry.

No production setting or deployment was changed. Native draft stop controls
require Bot API 10.3; see [streaming](ai-chat-streaming.md) and the
[server rollout procedure](../services/bot-api/README.md).

## Session identity

The dispatcher uses `FSMStrategy.USER_IN_TOPIC`. Middleware passes the resolved
`FSMContext.key` to the existing bounded store for both acquire and release.
This covers bot, chat, user, topic and the existing business/destiny fields;
unthreaded chats use `thread_id=None`. Each topic consumes a slot in the same
store. FSM and middleware storage belong to the dispatcher.

Callbacks use their source message's topic and callback sender. Inline callbacks
and inaccessible messages cannot load another conversation's data. Updates with
no resolved FSM receive a restart explanation instead of a user-only fallback.
The existing typed `UserData` dictionary, required deletion queue, active-handler
pins, TTL, capacity rejection and expired-session reset are retained.

AI replies, initialization, `/exit`, drafts, splits, media chat actions, and user
errors preserve the source topic. Administrator tracebacks remain operational
notifications. Stop updates use streaming's bot/chat/thread/draft registry and
source-owned generator closure; no `from_user` or injected FSM is required.

## Verification

`bot/tests/handlers/test_private_topics.py` exercises the production dispatcher,
context managers and bounded middleware with a local recording Bot session and
a controlled model stream. Scenarios cover simultaneous topics and an unthreaded
conversation, callbacks, reset/exit, stop/upstream failure, topic creation and
welcome failure, unsupported requests, capacity pressure and topic-local expiry.
The existing streaming tests cover long HTML splits and draft fallback routing.

```sh
make test FILE='bot/tests/handlers/test_private_topics.py bot/tests/middlewares bot/tests/handlers/test_chatgpt_drafts.py'
testgram run e2e/scenarios/chat_exit.yaml
```

The PR is based on `task-20261103-private-topics-prerequisites`, which integrates
the agreed retention, typing, streaming and enum context snapshots. Topic changes
are kept out of that base. Live Telegram smoke tests have not been performed.
