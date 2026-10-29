# Rich AI messages prototype

The opt-in adapter in bot/services/rich_messages.py is separate from
AnswerHandler. Production retains HTML streaming; no handler or model prompt
selects this experiment. The current StreamChunk producer supplies text and
reasoning, not a semantic tree. Integration needs a parser or structured-output
producer, the original text for history/fallback, and a live rendering trial.

## Adapter contract

The immutable ResponseParts tuple accepts TextPart, CodePart, MathPart,
ReasoningPart, QuotePart, DetailsPart, and ListPart. The function
to_rich_message(parts, draft=False, limits=...) returns InputRichMessage with
native blocks, without HTML or Markdown fields:

- Text and code preserve literal Unicode, angle brackets, and backticks.
  CodePart also accepts an optional language; MathPart keeps raw LaTeX.
- Quotes and details contain block tuples. Lists contain tuples of those tuples;
  start=None gives unordered items, otherwise decimal labels begin at start.
- Reasoning becomes thinking in a draft. The final message preserves it in
  collapsed details, because [thinking is draft-only](https://core.telegram.org/bots/api#inputrichblockthinking).

Default budgets are 16 block levels, 1000 nodes, and 256 KiB of block JSON.
List items count as nodes, not block levels; final reasoning adds a paragraph.
These are application budgets, not Telegram limits. Iterative preflight bounds
the tree and aggregate text before recursive Pydantic conversion. A final JSON
size check includes structural overhead and Unicode ASCII escapes. With the
default json.dumps serializer its character count equals its byte size; custom
session serializers may produce different sizes. Both checks are needed:
preflight limits conversion work, while the final check bounds the payload.

## Delivery and lifecycle

Create one RichMessagePrototype(bot, source, enabled=True) per response; enabled
defaults to False. Disabled/unsupported-server mode, groups, channels, and
business messages select the caller's existing HTML path. Unspecified server
support probes with a rich request, once per response until the first failure.

- The async send(parts, html_final) method returns Message. The no-argument async
  callback must return a Message, such as the last HTML chunk.
- The async send_draft(parts, draft_id, html_preview) method returns bool and
  requires a stable non-zero ID. Its no-argument async callback returns bool.
  Requests use can_stop=True and keep_on_stop=False; completion requires send.
- Rich requests preserve source chat/topic context even when is_topic_message
  is false. The final message also replies to the source message.

Conversion failure or explicit API rejection calls the fallback. The instance
then stays on HTML for remaining previews and finalization, avoiding repeated
failed rich requests. RetryAfter observes the cooldown first. Draft network/5xx
failures also fall back. Final network/5xx failures propagate because delivery
is ambiguous and another send could duplicate the response. Callback errors and
cancellation propagate.

The caller owns the original response, model stream closure, FSM/history,
retention, and stop registration. Reuse the [streaming lifecycle](ai-chat-streaming.md)
and existing split_response or _stream_to_message fallback without truncation
or another model request. This prototype does not supply private-topic/FSM
isolation or replace required context approval/retention decisions.

## Comparison and checks

Run the existing fixtures and checks:

    PYTHONPATH=bot .venv/bin/python -m tests.benchmarks.rich_messages --iterations 100
    make test FILE='bot/tests/services/test_rich_messages.py bot/tests/handlers/test_chatgpt_rich_fallback.py'
    make lint FILE=bot/services/rich_messages.py

The local baseline from 2026-10-23, implementation commit 55db4f6, used Python
3.13.11, aiogram 3.31.0, and Pydantic 2.12.5. Over 100 iterations, mixed content
took 0.0633 ms median/702 bytes for rich and 0.0101 ms/191 bytes for HTML.
Rich details trees at 4/8/16 levels took 0.0239/0.0430/0.0812 ms. A large Unicode
example took 0.4704 ms/217412 bytes for rich and 0.8346 ms/128078 bytes for HTML.

Those measurements include construction and serialization, not network, full
HTML splitting, or Telegram layout. HTML retains math/list/quote markers as
text and has no expandable details; rich fixtures encode native blocks.
The retained tests check literal content, nested ordering, depth/node/escaped
payload bounds, complete HTML fallback output and topic, cooldowns, cancellation,
and duplicate-send prevention. A subprocess bounds 16-level conversion to
10 seconds without imposing a flaky millisecond CI threshold.
The [aiogram 3.29.1 fix](https://docs.aiogram.dev/en/latest/changelog.html) explains
the discriminated-union change that removed exponential nested validation.

Keep production disabled until a controlled Telegram comparison measures
rendering, first-preview/final-send latency, and failure behavior. Follow the
[server rollout instructions](../services/bot-api/README.md); a pinned image does
not establish the running server version or stop-control support. Drafts expire
after 30 seconds without updates. No live Telegram trial or deployment was done.
