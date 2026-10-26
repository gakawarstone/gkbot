# Command registry

`bot/configs/commands.py` defines the bot's user commands and their Telegram
menu descriptions. `USER_COMMANDS` is a string enum class. Its members can be
passed directly to aiogram `Command` and the custom `CommandWithPrompt` filter.

`USER_COMMANDS.as_list()` returns command values in alphabetical order for
`/list`. `USER_COMMANDS.as_dict()` supplies the names and descriptions used by
`DEFAULT_COMMANDS` and `DefaultCommands.set`. Both menus contain the same 22
commands as the handlers registered by `handlers.setup` and `modules.setup`.
`/start`, `/sub`, and the retired Notion commands are absent.

To add a command:

1. Add a name and description to `_UserCommands`.
2. Register its handler using `USER_COMMANDS.<name>` and include its setup in
   the production router setup. Do not register a separate string literal.
3. Run `make test FILE=bot/tests/handlers/test_command_registry.py`.

The tests inspect production command filters, including commands nested in
`and_f` and `or_f`, feed module registrations, and prompt filters. They require
registered command names to match the registry, reject duplicate registrations,
and compare the names with `/list` and the configured Telegram menu.
Adding an advertised command without a handler fails these tests.

Command filters retain their existing restrictions. `/admins` works in groups;
`/img` needs a prompt and `/wait` needs minutes followed by message text.
Advertising a command does not change its FSM behavior or service requirements.
