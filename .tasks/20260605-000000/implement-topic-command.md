# Add private topics for separate AI sessions

- STATUS: OPEN
- PRIORITY: 2

## Problem

Telegram private topics could isolate several AI conversations for one user. The current FSM and middleware data are keyed by user, so adding `/topic` without thread-aware storage would mix conversation state between topics.

## Plan

1. Define whether `/topic` creates an AI session, selects an existing session, or only demonstrates Telegram topics.
2. Confirm that the bot and user can create private topics.
3. Choose an FSM key strategy that includes `message_thread_id` and migrate any related middleware context.
4. Pass the thread ID to messages, chat actions, drafts, and error responses produced inside a topic.
5. Register the command only after the behavior and fallback for unsupported chats are defined.
6. Add tests for two simultaneous topics owned by the same user.

## Acceptance criteria

- Two private topics for one user keep separate FSM and AI conversation state.
- Replies, status updates, drafts, and errors stay in their source topic.
- Unsupported chats receive a clear response and do not enter a partial FSM flow.
- Topic tests and static checks pass.

## History

Previous experimental changes were removed from:

- `bot/configs/commands.py`
- `bot/handlers/user/__init__.py`
- `bot/handlers/user/topic.py`

Expected implementation should define the intended user behavior before wiring the command into the user router.

Removed experimental code:

```diff
diff --git a/bot/configs/commands.py b/bot/configs/commands.py
@@
+    topic = "topic"

diff --git a/bot/handlers/user/__init__.py b/bot/handlers/user/__init__.py
@@
+from . import topic
@@
+    topic.setup(r)

diff --git a/bot/handlers/user/topic.py b/bot/handlers/user/topic.py
new file mode 100644
--- /dev/null
+++ b/bot/handlers/user/topic.py
@@
+from aiogram import Router
+from aiogram.filters import Command
+from aiogram.types import Message
+
+from configs.commands import USER_COMMANDS
+
+
+async def create_topic(m: Message):
+    await m.answer("i m creating topic for you")
+    print("dice")
+    dice = await m.answer_dice()
+    print(m.direct_messages_topic)
+    print(dice)
+    # await m.bot.create_forum_topic(m.from_user.id, "TEST")
+
+
+def setup(r: Router):
+    r.message.register(create_topic, Command(commands=USER_COMMANDS.topic))
```
