# Feed processor failures

`GkfeedItemProcessorExtension._run_processor(item, processor, processor_name)`
is the shared execution boundary. Generic web dispatch supplies `_process_base_item`.
A registry entry supplies its resolved `source_id` as `processor_name` and
call this same boundary for `entry.process`. Resolve and match entries outside
the boundary so configuration and matching errors propagate.

`RECOVERABLE_FEED_ERRORS` in `bot/modules/feed/handlers/_exceptions.py` is the
allowlist for the plain-link fallback:

- `FeedMediaExtractionError` for explicitly validated missing or malformed
  external media. Instagram, Shikimori, Twitch and VK use this type instead of
  generic `ValueError` or `TypeError`.
- `HttpRequestError`, aiohttp `ClientConnectionError`, `ClientPayloadError`,
  `ClientResponseError`, and `TimeoutError` for failed downloads and responses.
- Matreshka `InvalidMatreshkaVideoUrl` and `MatreshkaVideoUnavailable`, TikTok
  `TikTokInfoExtractionFailed`, `TikTokInvalidUrl` and
  `TikTokVideoUrlExtractionFailed`, and YouTube `UnavailableVideo`.
- aiogram `TelegramBadRequest`, `TelegramNetworkError` and
  `TelegramServerError`. In installed aiogram 3.26.0, `TelegramEntityTooLarge`
  inherits `TelegramNetworkError` and is also recoverable.

The external exception categories follow the
[aiohttp client exception reference](https://docs.aiohttp.org/en/stable/client_reference.html#client-exceptions)
and [aiogram error reference](https://docs.aiogram.dev/en/v3.26.0/dispatcher/errors.html).
The imported symbols and inheritance were also checked against the locked
aiohttp 3.13.3 and aiogram 3.26.0 packages.

Do not catch generic `Exception`, `ValueError`, `TypeError`, `KeyError`,
`IndexError`, `OSError` or `TelegramAPIError` at this boundary. Missing methods,
invalid call signatures, unexpected response shapes and invalid handler state
must retain their original exception object and traceback. Telegram forbidden,
unauthorized and retry-after errors, and task cancellation, also propagate.
Translate an expected content failure into `FeedMediaExtractionError` where
that content is validated, rather than widening the shared allowlist.

On a recoverable failure, the boundary logs item ID, feed ID, text length,
processor identity limited to 80 characters, exception class and original
stack frames. The logged exception is a redacted wrapper. Original exception
messages and chains are omitted because they can contain URLs, credentials
or media payloads. Neither the item nor its title, link or text is logged.
Unexpected exceptions propagate unchanged. A failure of `_send_item` also
propagates, with no recursive fallback.

Reddit's Telegraph path uses the shared boundary instead of a local blanket
catch. Existing photo and YouTube helpers still handle their own specific
`TelegramBadRequest` and `UnavailableVideo` fallbacks.
