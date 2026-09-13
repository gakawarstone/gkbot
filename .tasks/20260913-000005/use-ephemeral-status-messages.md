# Use ephemeral status messages in groups

- STATUS: OPEN
- PRIORITY: 3

## Problem

Download and processing handlers post ordinary status messages such as "Подождите" and delete them later. In busy group chats these messages create noise, and cleanup failures leave stale messages behind. Bot API 10.2 supports ephemeral messages visible only to the requesting user.

## Plan

1. Inventory temporary status messages across text, callback, download, and generation handlers.
2. Introduce a helper that sends ephemeral status messages when the chat and server support them.
3. Keep normal messages with existing cleanup behavior as a fallback.
4. Support editing and deleting both response types through one interface.
5. Add private-chat, group-chat, unsupported-server, and cleanup-failure tests.

## Acceptance criteria

- Supported group flows show transient status only to the requesting user.
- Private chats and older servers continue to work.
- Handlers do not depend on ephemeral-only fields when using the fallback.
- Status-message tests and static checks pass.

