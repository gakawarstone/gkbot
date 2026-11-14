# Feed processor failures

`_run_processor(item, processor, processor_name)` owns the plain-link fallback.
Registry dispatch calls `await self._run_processor(item, entry.process, entry.source_id)`;
legacy dispatch supplies the method name. Resolve and match entries outside this
boundary so configuration and matching errors propagate.

The exact recoverable exceptions are defined in
[`RECOVERABLE_FEED_ERRORS`](../bot/modules/feed/handlers/_exceptions.py).
Use `FeedMediaExtractionError` at validation points for missing or malformed
external media. Catching generic `ValueError`, `TypeError` or `Exception` at the
shared boundary would also hide programming errors. Unexpected errors,
cancellation and Telegram authorization or rate-limit errors propagate unchanged.
If the plain-link send fails, that error also propagates without another fallback.

Recoverable failures log item ID, feed ID, text length, processor identity limited
to 80 characters, exception class and original stack frames. A fresh exception
containing only the original class name replaces messages and chains that could
expose URLs, credentials or payloads. The item, title, link and text are not logged.
