# Ephemeral status constraints

[Telegram's delivery rules](https://core.telegram.org/bots/api#ephemeral-messages-and-commands)
allow any bot to respond ephemerally within 15 seconds of an eligible callback.
For ordinary incoming text, the bot must be a group administrator. Delivery to
offline users is not guaranteed. Callback recipients must come from
`callback.from_user`, since the keyboard message usually belongs to the bot.

Bot API 10.2 uses `receiver_user_id` and `callback_query_id`; 10.3 uses
[`EphemeralMessageParameters`](https://core.telegram.org/bots/api#ephemeralmessageparameters).
Sending both formats keeps one request compatible with both versions. A server
that ignores these fields can return an ordinary message, which must be reused
without sending a duplicate. Explicit eligibility/capability rejections allow an
ordinary fallback. Network failures and unrelated errors propagate without
retrying a potentially successful send.

`temporary_status` owns cleanup; `StatusMessage` routes edits and deletion to the
ordinary or ephemeral API. Cleanup errors must not hide failure or cancellation.
`keep()` preserves an edited error notice. Successful deletion is tracked
separately, so final cleanup cannot delete the same ephemeral ID again after
`publish()`; Telegram may reuse expired or deleted ephemeral IDs.

Generation uses `publish()` to replace the waiting notice with a persistent,
ordinary response. Making the final response ephemeral would change its
visibility and lifetime. In groups, personal statuses leave the shared keyboard
intact; private chats and explicit fallbacks retain ordinary-message behavior.
