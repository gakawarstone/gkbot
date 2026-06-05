# /topic command

- STATUS: OPEN
- PRIORITY: 2

Implement `/topic` command support.

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
