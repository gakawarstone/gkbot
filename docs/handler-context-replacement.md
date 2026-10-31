# Proposal to replace handler context field lookup

Status: proposed, awaiting explicit task-owner approval before runtime work.
This documentation PR does not record that approval.

Audited on 2026-10-23 at `dfdecceb2e97824e924538bf7720c2547a7156a7`, using
Python 3.13.11 and the locked aiogram 3.26.0 installation.

## Recommendation

Keep the six dataclass context schemas and their existing flat storage keys.
Replace expression-based field lookup with explicit string keys and validate
current field types and the elements of `messages` on reads and writes. Keep
the synchronous manager API over the mapping supplied as `handler.user_data`. This removes
`varname` without changing storage ownership, FSM state names, or user flows.

The proposed call contract is:

```python
self.set("file_name", self.event.text)
self.clean_context("book_id", "property_name")
context = self.ctx
```

`ctx` remains a typed dataclass view. `props` remains the schema class, but callers
stop passing `self.props.field` or `self.ctx.field` as keys. The arguments of
`clean_context` are explicit keys to preserve, matching today's exclusion behavior.
An unknown set or exclusion key raises `KeyError` before any mutation. A wrapper
may forward the strings normally; caller stack depth has no meaning.

Use `dataclasses.fields` for schema fields and `typing.get_type_hints` for resolved
annotations. Class methods and other non-field attributes must never become
stored fields. No rule compilation or cache is needed for these six small schemas.
Do not serialize the dataclass or replace the supplied mapping.

## What the current manager actually stores

`extensions/handlers/base.py` reads `self.data["data"]`, populated by
`middlewares/user_data.py`. Its class-level mapping is keyed only by Telegram user
ID and is shared by message and callback middleware instances. Context values are
ordinary Python objects in that mapping, separate from `FSMContext` data.
`core/bot.py` configures aiogram `MemoryStorage` for FSM state and FSM data.

There are six production schemas with 16 fields. Every field currently defaults
to `None`. The paths below are relative to `bot/handlers/user/`.

### ChatGPT

Schema `_ChatGPTContext`, manager `ChatGPTContextManager`, defined in
`chatgpt/_context.py`.

- `messages`: currently `Optional[list]`; propose `list[str] | None`.
- `chatgpt/_base.py` mixes the manager into message handlers.
- `chatgpt/init.py`, `InitHandler`, clears the context, sets a fresh list in its
  `clean_context` override, and appends a system instruction.
- `chatgpt/answer.py`, `AnswerHandler`, appends the prompt and generated answer,
  and joins the history for the model request.

Keep the three existing appends and prompt/history behavior. Their writers
produce strings; validate the stored list on context reads and explicit sets,
without copying history or introducing a mutation wrapper. Update the cleanup
override to `*preserve: str` and keep its fresh-list initialization.
`chatgpt/exit.py` delegates to the shared FSM exit handler and does not use
this manager.

### Download

Schema `_DownloadContext`, manager `DownloadContextManager`, defined in
`download/_context.py`.

- `file_name`: `Optional[str]`, stored from message text.
- `download/_base.py` mixes the manager into message handlers.
- `download/init.py`, `InitHandler`, clears the filename.
- `download/get_name.py`, `GetNameHandler`, writes it.
- `download/download.py`, `DownloadHandler`, reads it for `FSInputFile`.

Use the literal `"file_name"` for writes. Preserve the optional read and existing
download behavior. Message deletion queues are middleware data, outside this schema.

### Reminder

Schema `_ReminderContext`, manager `ReminderContextManager`, defined in
`reminder/_context.py`.

- `text`: `Optional[str]`, from message text.
- `tz`: `Optional[timedelta]`, supplied by timezone middleware and the timezone
  handler extension.
- `date`: `Optional[datetime.date]`, produced by date parsing.
- `time`: `Optional[datetime.time]`, produced by time parsing.
- `message`: `Optional[aiogram.types.Message]`, the live widget message.
- `reminder/_base.py` reads the widget message and text/date/time to render it.
- `reminder/start.py`, `InitHandler`, preserves `"tz"` during cleanup and writes
  the timezone and widget message.
- `reminder/get_text.py`, `TextInputHandler`, writes text.
- `reminder/get_date.py`, `DateInputHandler`, writes the parsed date.
- `reminder/get_time.py`, `TimeInputHandler`, writes the time and invokes
  `CreateRemindHandler` with the same user-data mapping.
- `reminder/create.py`, `CreateRemindHandler`, reads text/timezone/date/time and
  renders the final widget through the base handler.

Keep the literal keys and live `Message` reference. The nested creation handler
currently receives no `state` argument; the proposed synchronous manager must not
introduce an FSM dependency into its context reads.

### Road settings

Schema `RoadSettingsContext`, manager `RoadSettingsContextManager`, defined in
`road/settings/_context.py`.

- `setting_name`: `Optional[str]`, parsed from the settings callback.
- `setting_new_value`: `Optional[Any]`; its only current writer produces a
  timezone-aware `datetime.time` in `_validate_time`.
- `road/settings/callback.py`, `EditSettingsHandler`, clears the schema and writes
  the name from a callback.
- `road/settings/edit/get_new_setting_value.py`, `GetNewSettingValueHandler`,
  writes the parsed time and reads both fields for the repository update.

Keep `Any` in this migration to avoid combining a settings schema change with the
manager replacement. It deliberately has no value validation. Narrowing it to
`time | None` can be a separate change. The menu-only `road/settings/_base.py`
and `start.py` do not inherit or consume the context manager.

### Add book

Schema `_AddBookContext`, manager `AddBookContextManager`, defined in
`books/messages/add/_context.py`.

- `name`, `author`: `Optional[str]`, from message text.
- `chapter_cnt`: `Optional[int]`, from `int(message.text)`.
- `message`: `Optional[aiogram.types.Message]`, the live creator widget.
- `books/messages/add/_base.py` reads all fields to render/edit the widget.
- `start.py`, `InitAddBookHandler`, clears the context and stores the widget.
- `get_name.py`, `GetNameHandler`, and `get_author.py`, `GetAuthorHandler`, write
  their corresponding fields and render the widget.
- `get_chapters_cnt.py`, `GetChaptersCnt`, writes the count and constructs
  `CreateBookHandler` with the same state and user-data mapping.
- `create.py`, `CreateBookHandler`, reads name/author/count for model creation
  and renders the result.

Replace the four writer keys with string literals. Keep widget identity and
the nested-handler mapping handoff.

### Edit book property

Schema `_EditBookPropertyContext`, manager `EditBookPropertyContextManager`,
defined in `books/messages/edit_property/_context.py`.

- `property_name`, `new_value`: `Optional[str]`, from callback data and message text.
- `book_id`: `Optional[int]`, from the selected book model.
- `books/callbacks/edit_properties.py`, `EditHandler`, writes ID/property and
  constructs the message initialization handler with the same mapping and state.
- `books/messages/edit_property/_base.py` supplies the shared manager inheritance.
- `start.py`, `InitEditBookPropertyHandler`, preserves `"book_id"` and
  `"property_name"` during cleanup and reads the property for the prompt.
- `get_new_value.py`, `GetNewPropertyValueHandler`, writes the new value and
  passes the mapping/state to `ChangeBookPropertyHandler`.
- `change_property.py`, `ChangeBookPropertyHandler`, reads all fields for the
  repository update.

Keep the callback-to-message handoff. `choose_book.py` and `choose_property.py`
only build selection UI and do not consume the manager.

### Shared consumers and tests

The generic, message, and callback base handlers expose the same `user_data`
contract. `TimeZoneMiddleware` writes `"tz"` directly, and
`UseTimeZoneHandlerExtension` reads it directly. `DeleteQueueMiddleware` and
`OneTimeMessageHandlerExtension` own `"delete_queue"`. Cleanup must preserve
unrelated keys, including this queue, and the reminder exclusion must preserve
the shared timezone value.

`bot/tests/contrib/test_context.py` defines the only additional `BaseContext`
subclass, `FakeContext`, with `Optional[str]`, `Optional[int]`, and `Optional[Any]`.
Its `FakeContextManager` uses a shared class-level dictionary. The seven tests
cover missing reads, schema/view type, writes, cleanup, and single/multiple
exclusions. `test_make_prop.py` has one test of expression-derived keys.

Direct FSM users, such as `handlers/user/tasks.py` and
`modules/feed/handlers/auth/get_login.py` / `get_password.py`, do not consume
`BaseContextManager`. Their `FSMContext` keys and data APIs stay outside this
migration. No other production context schema or manager import was found by a
repository-wide import/base-class and call-site inventory.

## Alternatives considered

1. Explicit keys with the existing dataclass view, recommended. Keep typed
   `ctx.field` reads and check string keys against the schema at runtime.
2. Dataclass serialization. `asdict` copies objects and does not validate types.
   Serializing live widget messages is unnecessary; retain dataclasses as views.
3. `TypedDict`. Literal indexing helps static checking but needs the same runtime
   validation and changes every `ctx.field` read. It adds migration work here.
4. Direct aiogram FSM data. Installed aiogram 3.26.0 has asynchronous `get_data`,
   `set_data`, and `update_data`. Moving the fields there changes storage ownership,
   requires state in nested handlers, and changes cleanup. `FSMContext.clear()`
   clears FSM data, but currently leaves middleware data alone. The middleware
   is per-user; Dispatcher defaults to `FSMStrategy.USER_IN_CHAT`. Those are
   separate storage/isolation decisions.

## Runtime validation policy to approve

Support the annotations actually needed by these schemas: nullable concrete
classes, `Any`, and `list[str] | None`. Accept both `Optional[T]` and `T | None`
spellings. Keep one validation helper shared by reads and writes; no validator
registry, compiled rules, or custom exception class is needed.

- For concrete classes, retain today's exact type check, including `str`, `int`,
  `date`, `time`, `timedelta`, and `Message`. This preserves existing behavior
  and rejects `bool` for `int` and `datetime` for `date`. `Any` accepts any value.
- For `list[str]`, require a concrete list and check every element is a concrete
  string. Empty lists are valid; `["a", 1]` is invalid. Use `get_origin` and
  `get_args` to recognize the annotation. Do not compare `type(value)` with
  `list[str]`. No current field needs dictionaries, nested containers, or
  multi-type unions, so do not add support for them in this migration.
- All current fields default to `None`. Missing keys read as `None` without
  insertion; explicit `None` is valid for nullable fields and `Any`. Reject an
  unsupported annotation with `TypeError`, rather than silently skipping checks.
- Validate all schema fields on `ctx` reads and the target field on `set`.
  Raise the existing `ValueError` for a value mismatch, adding the schema/key,
  failing list index when applicable, and expected/actual type. Never include
  stored values. Failed reads/writes must leave the mapping unchanged.
- `clean_context(*preserve: str) -> None` checks every exclusion key first, then
  sets only this schema's other keys to `None`, including absent keys. It must
  recover invalid old values and preserve unrelated data without reading it.
- Keep object identity, including live `Message` objects and history lists.
  Direct middleware writes and in-place list mutation bypass `set`; validate
  them on the next `ctx` read. This matches the existing mutable mapping contract.

## Migration and session compatibility

After owner approval, make one runtime change in the existing manager package:

1. Replace stack-based lookup with dataclass field discovery and explicit keys.
   Keep `BaseContext`, `BaseContextManager`, `props`, `ctx`, and `user_data`.
   Convert all writers/exclusions listed above, update the ChatGPT cleanup
   override, and change its annotation to `list[str] | None` together.
2. Update the tests below and remove obsolete `Property` and stack-inspection
   helpers. Once no consumers remain, remove the direct `varname` dependency
   and regenerate the lockfile and requirement exports using repository commands.

Keep storage keys, FSM state names, mapping handoffs, and `state.clear()` behavior.
Valid existing values need no conversion. ChatGPT histories containing non-strings
will now fail validation; do not silently filter or coerce them. An explicit
ChatGPT restart clears that history and initializes a fresh list. Cleanup must
work even when old values fail validation.

Both current stores are in memory and lose sessions on process restart. Test
compatibility by prepopulating mappings with the old key/value layout, without
adding a serializer or a session migration system. Old expression-based callers
and new string-key callers must change together; no stack-based compatibility
adapter is proposed.

The shared flat `"message"` key and per-user scope remain existing limitations.
Private-topics work owns mapping isolation by `bot/chat/user/message_thread_id`
and draft/status/error routing. Its mapping should enter through `user_data`;
this manager does not determine session identity. This proposal is not an
implemented runtime prerequisite for that work.

## Required checks for the runtime PR

- Preserve the seven existing manager tests with explicit keys and fresh mappings.
  Replace the `make_prop` test with variable/wrapper key tests. Check unknown
  set/exclusion keys cause no mutation, even after a valid exclusion, and schema
  methods are not treated as fields.
- Test concrete types, `Any`, nullable fields in both spellings, empty/populated
  `list[str]`, wrong outer/element types, and unsupported annotations. Cover read
  and write paths, error messages without values, and detection of an invalid
  direct list mutation on the next read.
- Prepopulate all six legacy contexts and test reads, updates, and cleanup.
  Preserve widget/list identity, unrelated keys, `delete_queue`, the reminder
  timezone exclusion, and both book-edit exclusions. Cleanup must recover invalid
  data without partial mutation.
- Check ChatGPT initialization and answer history order, add-book and reminder
  completion, download filename use, and both callback-to-message flows for book
  editing and road settings. Keep the same mapping in nested handlers and the
  existing FSM transitions; mock external I/O.
- Run the context and middleware tests, the full suite, and lint on changed Python
  files. Distinguish existing lint findings from new ones.

## Evidence for this documentation PR

Baseline checks on 2026-10-23:

- `make test FILE=bot/tests/contrib`: 8 passed, with two existing `varname`
  warnings about fallback evaluation.
- `make test`: 105 passed, 13 skipped, five existing warnings.
- `make lint FILE=bot/extensions/handlers/context_manager`: stopped at 13
  existing Ruff findings in unchanged code; later lint stages did not run.
  This documentation PR does not repair those findings.

Self-review on 2026-10-26 checked the proposal against the original task and
current consumers: all six schemas, 16 fields, six managers, and 24 consumer
classes remain covered. Documentation links, example syntax, whitespace, and the
documentation-only diff passed checks. `make test` again passed with 105 passed,
13 skipped, and five existing warnings. Lint was not repeated for text changes.

API choices were checked against the installed aiogram symbols/signatures and
these official references:

- [Python 3.13 dataclasses](https://docs.python.org/3.13/library/dataclasses.html)
  for field discovery, `asdict` copy semantics, and annotation handling.
- [Python 3.13 typing](https://docs.python.org/3.13/library/typing.html)
  for `TypedDict`, runtime annotation limits, `get_type_hints`, `get_origin`,
  and `get_args`.
- [aiogram 3.26.0 storage documentation](https://docs.aiogram.dev/en/v3.26.0/dispatcher/finite_state_machine/storages.html)
  and [Dispatcher source](https://github.com/aiogram/aiogram/blob/v3.26.0/aiogram/dispatcher/dispatcher.py)
  for storage choices and the default FSM strategy. The installed
  `aiogram/fsm/context.py` confirms the async data methods and `clear` behavior.

## Owner decision

Approve the explicit-key dataclass view, current-type validation plus `list[str]`,
and preservation of the storage boundary, or choose an alternative above.
The task stays open until the decision is recorded. Runtime remains unchanged.
