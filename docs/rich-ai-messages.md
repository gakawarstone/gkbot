# Rich AI messages prototype

The module bot/services/rich_messages.py is an opt-in experiment with native
Telegram blocks. It is separate from AnswerHandler; production AI chats retain
the HTML streaming path. There is no environment switch or automatic activation.

This branch includes [streaming prerequisite PR #39](https://github.com/gakawarstone/gkbot/pull/39)
at e24bebba1d1b697768cd72f0496472a63427e7d2, including its splitter prerequisite
[PR #20](https://github.com/gakawarstone/gkbot/pull/20). The prototype PR uses the
streaming branch as its base, excluding those prerequisite diffs.
See [streaming and cancellation contracts](ai-chat-streaming.md).

## Parts and blocks

The function to_rich_message(parts, draft=False, limits=...) returns an
InputRichMessage with blocks, without its HTML or Markdown fields. The semantic
input parts are immutable dataclasses:

- TextPart(text) becomes a paragraph.
- CodePart(text, language=None) becomes preformatted code.
- MathPart(expression) becomes a mathematical-expression block with raw LaTeX.
- ReasoningPart(text) becomes thinking in a draft. In a final message it becomes
  collapsed details with summary "Reasoning" and a paragraph, preserving the
  text without including a draft-only block.
- QuotePart(blocks, credit=None) becomes a block quotation.
- DetailsPart(summary, blocks, is_open=False) becomes expandable details.
- ListPart(items, start=None) becomes a list of block tuples. With start, items
  receive decimal labels beginning at that value; otherwise it is unordered.
  Lists, quotes, and details may contain other parts.

For example, the following requires no manual HTML tags:

    from services.rich_messages import (
        CodePart, DetailsPart, ListPart, MathPart, ReasoningPart, TextPart,
        to_rich_message,
    )

    parts = (
        ReasoningPart("Check the equation"),
        TextPart("Пример <&> 😀"),
        CodePart("print('<&>')", language="python"),
        ListPart(((TextPart("first"),), (MathPart("x^2 + y^2 = z^2"),)), start=1),
        DetailsPart("More", (TextPart("additional explanation"),)),
    )
    draft = to_rich_message(parts, draft=True)
    final = to_rich_message(parts)

The current model producer supplies only StreamChunk(text, "content" | "reason"),
not a parsed tree. This prototype defines and exercises a semantic-parts
contract. It does not parse raw Markdown, change model prompts, or automatically
classify code and lists in model text. A future handler integration must supply
a parser or structured model output, retain the original text for history and
fallback, and compare live rendering before activation. The benchmark provides
paired semantic and Markdown fixtures for the same examples.

## Sending and fallback

Create one RichMessagePrototype(bot, source, enabled=True) per response.
The default is enabled=False. This private-chat experiment also bypasses rich
sends for groups, channels, business messages, or server_supports_rich=False.
Leave server support unspecified to probe with the first rich request.
A successful request does not prove stop-control support on an older server.

The async send(parts, html_final) method persists a response and returns a
Message. Its no-argument async fallback must return a Message, such as the last
message produced by the existing HTML path. The rich request copies the source
chat and message_thread_id explicitly, even if is_topic_message is false, and
replies to the source message.

The async send_draft(parts, draft_id, html_preview) method returns bool. The
caller provides a stable, non-zero draft ID and a no-argument async HTML preview
callback returning bool. Rich drafts use can_stop=True and keep_on_stop=False.
Completion must call send; a draft alone is temporary.

Conversion failure or an explicit Telegram API rejection selects the callback
once. The instance then stays on HTML for the rest of that response, including
subsequent previews and finalization. A fresh response can probe again.
TelegramRetryAfter waits for the supplied cooldown before fallback. Draft
network and server failures also select HTML. Final-send network and 5xx errors
propagate, because the server may already have persisted the message; retrying
via HTML could duplicate it. This matches the streaming prerequisite's policy
for ambiguous final-message delivery. Callback errors and CancelledError
propagate without retry.

The callback owns the original response and source context. It must use the
existing split_response or _stream_to_message path, without truncation or a new
model request. Tests exercise the actual edit/split implementation with a large
rejected rich response, preserving every rendered character and the topic.

The adapter does not own model streaming, cancellation registration, FSM state,
history, or context retention. Future handler integration must reuse
_private_response, active_generations, stop_generation, and stream closure from
PR #39. This experiment does not establish topic/FSM isolation or change any
required approval or retention policy for private topics.

## Limits and validation

The default budgets are 16 block levels, 1000 nodes including list items and
the extra final reasoning paragraph, and 256 KiB for serialized block JSON.
These are application budgets, not claimed Telegram limits. List-item wrappers
count as nodes but do not add a block level. An iterative walk checks depth,
width, and aggregate text size before recursive conversion. Conversion then
checks JSON size with Python's default json.dumps, matching aiogram's default
serializer and its ASCII escapes for Unicode. A custom session serializer can
have different wire sizes. Over-budget output selects the unchanged HTML
fallback, rather than dropping or clipping parts.

The installed aiogram 3.31.0 uses discriminated input-block unions. Its
[3.29.1 changelog](https://docs.aiogram.dev/en/latest/changelog.html) describes
the fix for exponential nested-block validation. Tests validate nested input
JSON, a large response at the depth limit, and rejection of a 2000-level tree
before recursive conversion. A subprocess watchdog gives the benchmark
fixtures, including the 16-level tree, a generous 10-second bound. No
millisecond threshold is imposed on shared CI.

## Local comparison

Run without a bot token or network access to Telegram:

    PYTHONPATH=bot .venv/bin/python -m tests.benchmarks.rich_messages --iterations 100

On 2026-10-23 with Python 3.13.11, aiogram 3.31.0, and Pydantic 2.12.5, median
conversion plus serialization times over 100 iterations were:

- Plain text: rich 0.0096 ms and 100 bytes; HTML 0.0023 ms and 31 bytes.
- Mixed reasoning, code, lists, math, quote, and details: rich 0.0633 ms and
  702 bytes; HTML 0.0101 ms and 191 bytes.
- Details trees with 4, 8, and 16 block levels: rich 0.0239, 0.0430, and
  0.0812 ms respectively. HTML flattens the corresponding examples to text.
- Large Unicode response: rich 0.4704 ms and 217412 bytes; HTML 0.8346 ms and
  128078 bytes. This response exceeds normal-message limits and would require
  the existing splitter on the HTML path.

The HTML renderer supports bold and code, while list labels, math delimiters,
and quote markers remain text; it has no native expandable details. Rich
fixtures carry these as native blocks, with literal special characters preserved
in string values. Tests assert the native payload, not a simulated Telegram
client screenshot. The numbers above measure construction and encoded content
fields only. They exclude the network, request envelopes, full HTML splitting,
and Telegram client layout, so they do not establish end-to-end latency or
visual parity. Rich conversion includes its budget checks.

Locally tested failure behavior differs at explicit final-message rejection:
the experiment invokes HTML fallback, while the existing final HTML path
propagates API errors. Both propagate ambiguous final delivery and cancellation.
The experiment sends no rich requests when disabled and stops trying rich after
the first failed preview. Successful draft/final tests use real aiogram methods
with a recording session and no HTML or Markdown fields in the rich request.

The running server was reported as Bot API 9.5 by the prerequisite audit; the
Compose image is pinned to 10.3. Neither this change nor merging that pin deploys
it. Follow [server rollout instructions](../services/bot-api/README.md).
Live client rendering, time to first preview, final-send latency, and failure
behavior against both server versions still need a controlled Telegram trial.
Keep the experiment disabled in production until that comparison is complete.

## Checks

    make test FILE='bot/tests/services/test_rich_messages.py bot/tests/handlers/test_chatgpt_rich_fallback.py bot/tests/handlers/test_chatgpt_drafts.py bot/tests/handlers/test_chatgpt_answer.py'
    make test
    make lint FILE='bot/services/rich_messages.py bot/tests/services/test_rich_messages.py bot/tests/handlers/test_chatgpt_rich_fallback.py bot/tests/benchmarks/rich_messages.py'

Results: 129 focused tests passed; the full suite passed with 253 passed and
13 skipped. All four new Python files pass Ruff, typos, mypy, and pyright.
Full make lint stops at 381 existing Ruff findings. A separate archive of the
prerequisite commit produces the same count. No production handler, dependency,
deployment, root checkout, or .env was changed by this prototype.

## Official API contract

- [InputRichMessage](https://core.telegram.org/bots/api#inputrichmessage) requires
  exactly one of blocks, HTML, or Markdown.
- [RichText](https://core.telegram.org/bots/api#richtext) accepts plain strings.
  There is no RichTextPlain class in the installed wheel.
- [Input rich blocks](https://core.telegram.org/bots/api#inputrichblock) define
  paragraph, preformatted code, math, lists, quotes, and details.
- [Thinking blocks](https://core.telegram.org/bots/api#inputrichblockthinking)
  are draft-only and cannot appear in a persisted message.
- [Rich drafts](https://core.telegram.org/bots/api#sendrichmessagedraft) target
  private chats, expire after 30 seconds, and require a persistent final send.
- [aiogram list items](https://docs.aiogram.dev/en/latest/api/types/input_rich_block_list_item.html)
  expose numeric value and label type on outgoing list items. Incoming list
  items instead have a required rendered label; input and output JSON are
  different contracts.
