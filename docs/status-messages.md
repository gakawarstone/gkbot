# Temporary status messages

`utils.status_message.temporary_status(message, text, callback=..., reuse_message=...)`
owns the waiting notice and deletes it on success, failure or cancellation. Callers
receive a `StatusMessage` with `edit_text` and `delete`; they do not read Telegram
message identifiers or branch on response type. Cleanup errors from Telegram are
logged without replacing the operation's result or exception.

## Group delivery and fallback

For a group or supergroup with an identified human requester, the helper sends a
personal ephemeral status. Callback handlers use `callback.from_user`, not the
sender of the message containing the keyboard. They also pass the callback ID.
The shared keyboard is left intact, including when the old callback payload asks
to reuse it as a status message.

[Telegram's ephemeral delivery rules](https://core.telegram.org/bots/api#ephemeral-messages-and-commands)
allow any bot to respond within 15 seconds of an eligible callback. For ordinary
incoming text, the bot must be an administrator of the group. Telegram does not
guarantee delivery to offline users. No administrator lookup or permission cache
is needed; the send response determines which type of message was created.

The helper sends both the legacy `receiver_user_id` / `callback_query_id` fields
used by Bot API 10.2 and the
[`EphemeralMessageParameters`](https://core.telegram.org/bots/api#ephemeralmessageparameters)
object used by 10.3. Both formats are available in the pinned aiogram 3.31.0.

Private chats, channels, missing users, bot senders and anonymous text senders use
ordinary messages. A server that ignores the ephemeral parameters can return an
ordinary `Message`; the helper edits and deletes that same response without
sending a duplicate. An explicit ephemeral/recipient/callback capability or
eligibility rejection triggers the ordinary-message fallback, preserving the old
`reuse_message` behavior. Formatting errors, network failures and other unrelated
errors propagate without retrying a potentially successful send. There is no
permanent capability cache, so an upgraded server is used on the next request.

Ephemeral edits and deletion use the separate
[`editEphemeralMessageText`](https://core.telegram.org/bots/api#editephemeralmessagetext)
and [`deleteEphemeralMessage`](https://core.telegram.org/bots/api#deleteephemeralmessage)
methods, with the returned ephemeral ID and the requester ID. An ordinary
response only needs the usual message ID.

## Inventory and generation

The following processing notices use the helper:

- YouTube, VK, Pornhub and Porno365 callbacks through the shared download lifecycle.
- Matreshka and Sasflix audio callbacks.
- TikTok, Instagram post and short-video text download handlers.
- ChatGPT and image-description waiting notices.

TikTok and Instagram keep their existing error notices after editing them, through
`status.keep()`. Unexpected errors and cancellation still clean up the waiting
notice. Ephemeral error notices can expire in the client.

Generation uses `status.publish(text)` when the first response is ready. An
ordinary waiting message becomes the persistent response through an edit. An
ephemeral waiting message is deleted and a normal response is sent in the same
chat. Later streamed chunks edit that normal message, so generated answers keep
their previous visibility and lifetime. A generation failure before the first
response removes the waiting notice.

Menus, download-selection keyboards, FSM input prompts, final media, final
answers and scheduled notifications remain ordinary messages. The image-generation
prompt handler and document download handler have no waiting-message send site.

## Verification

The offline suite uses real aiogram request models and a mocked session transport.
It covers group/supergroup targeting, callback identity, forum topics, both wire
formats, private chats, ineligible senders, rejecting/ignoring old servers,
unrelated send errors, persistent generation results, download failures,
cancellation and cleanup errors. External Telegram and download smoke tests
remain opt-in; these checks do not deploy or contact a live Bot API server.
