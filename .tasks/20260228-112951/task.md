# Add /create_topic command to create forum topics

- STATUS: COMPLETED
- PRIORITY: 1

## Plan

1.  **Research & Verification**: Confirm `aiogram`'s `create_forum_topic` supports private chats. (Done)
2.  **Configuration**: Add `create_topic` to `USER_COMMANDS` in `bot/configs/commands.py`. (Done)
3.  **Handler Implementation**: (Done)
    - Create `bot/handlers/user/forum.py`.
    - Implement `/create_topic` handler which asks for a topic name.
    - Call `bot.create_forum_topic(chat_id=message.chat.id, name=name)` if chat is private.
4.  **Registration**: Register the new handler in `bot/handlers/user/__init__.py`. (Done)
5.  **Validation**: Ran lint and verified code structure. (Done)
