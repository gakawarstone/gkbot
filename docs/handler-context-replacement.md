# Proposal to replace handler context field lookup

Status: proposed, awaiting task-owner approval. No runtime change is authorized by
this document. The owner must explicitly approve this design in the task thread
before implementation starts; opening or merging this documentation PR alone
does not record that approval.

Audited on 2026-10-23 at `dfdecceb2e97824e924538bf7720c2547a7156a7`, using
Python 3.13.11 and the locked aiogram 3.26.0 installation.

## Recommendation

Keep the six dataclass context schemas and their existing flat storage keys.
Replace expression-based field lookup with explicit string keys and validate
values recursively against the schema on reads and writes. Keep the synchronous
manager API over the mapping supplied as `handler.user_data`. This removes
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
annotations. Compile/cache validation rules per schema class. Class methods and
other non-field attributes must never become stored fields. Do not serialize the
dataclass or replace the supplied mapping.

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

Keep the prompt/history behavior. Replace all three in-place appends with a new
list passed to `set("messages", ...)`, so writes pass element validation. Give
the cleanup override a typed `*preserve: str` signature and preserve its fresh-list
initialization. `chatgpt/exit.py` delegates to the shared FSM exit handler and
does not use this manager.

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

1. **Explicit keys with the existing dataclass view, recommended.** Smallest
   migration for all consumers. Schema annotations remain the source of validation
   rules. String keys need runtime membership checks; static checking alone cannot
   correlate a string argument with its value type. Per-schema `Literal` key
   aliases may help editors later, but are not required for correctness.
2. **Serialize dataclasses into stored dictionaries.** Field discovery removes
   stack inspection, but `asdict` recursively converts nested dataclasses and
   containers and deep-copies other objects. That is unnecessary for live widget
   messages. Dataclasses do not enforce annotation types. Whole-object writes can
   overwrite unrelated middleware keys unless carefully merged. Use dataclasses
   as views, without serialization.
3. **Typed mappings with `TypedDict`.** Literal indexing is explicit and useful
   for static checks, but runtime values are still dictionaries. This needs the
   same runtime validation policy, plus conversion of every `ctx.field` read and
   handling of absent keys. It offers too little benefit for this migration.
4. **Direct aiogram FSM data access.** `get_data`, `set_data`, and `update_data`
   exist in installed aiogram 3.26.0 and are asynchronous. Moving context there
   would change storage ownership, nested-handler requirements, mutable history
   writes, and session identity. The current middleware is per-user; the configured
   Dispatcher defaults to `FSMStrategy.USER_IN_CHAT`. `FSMContext.clear()` also
   clears FSM data, whereas today it leaves the separate middleware data alone.
   A future storage/isolation migration needs its own design and compatibility
   tests. It should not be hidden in a field-lookup replacement.

## Runtime validation policy to approve

- Resolve annotations from trusted schema classes once. Support `Any`, ordinary
  concrete classes, `None`, `Optional[T]`, `typing.Union`, `T | U`, `list[T]`, and
  `dict[K, V]`, including nested combinations. This is a deliberately bounded
  validator, not an implementation of the full Python typing language.
- For scalar `str`, `int`, `float`, `bool`, `date`, `time`, and `timedelta`, require
  the exact concrete type. Thus `bool` is rejected for `int`, and `datetime` for
  `date`. For other concrete classes use `isinstance`, so a `Message` subclass is
  accepted. `Any` accepts every value. Never coerce strings/numbers or deserialize
  dictionaries into messages.
- For `list[T]` and `dict[K, V]`, require the corresponding concrete outer type
  and validate every element or key/value recursively using `get_origin` and
  `get_args`. An empty container is valid; `list[str]` accepts `["a"]` and rejects
  `["a", 1]`. Do not pass a parameterized annotation to `isinstance` or compare
  it with `type(value)`.
- All current schemas are optional with a `None` default. Missing keys read as
  that default without inserting data. Explicit `None` is accepted only by
  nullable annotations or `Any`. This deliberately makes nullable writes
  consistent with existing nullable reads and cleanup.
- Reject unsupported annotations, unresolved references, unparameterized
  containers, or fields without a nullable `None` default as a schema
  `TypeError` before accessing or mutating storage. Tuples, sets, `Literal`,
  protocols, recursive schemas, and type aliases declared with `type` need an
  explicit future extension and tests. Remove the ChatGPT raw-list workaround
  in the same runtime change so it never encounters this rejection.
- Validate the entire schema view on `ctx` reads and the target value on `set`.
  A value mismatch raises `ContextValidationError`, a `ValueError` subclass,
  with schema, field/element path, expected type, and actual type. Do not include
  the value or chat history in errors. Invalid writes leave storage unchanged;
  invalid reads leave existing session data available for diagnosis or restart.
- `clean_context(*preserve: str) -> None` checks every exclusion first, then sets
  only this schema's other keys to `None`, including previously absent keys.
  It must work even if old values are invalid and leave all unrelated keys intact.
- Preserve object identity in the dataclass view, including the live widget
  message. Returned mutable containers remain aliases, as today; the manager
  cannot intercept arbitrary mutation or direct middleware writes. Revalidate on
  the next read. Migrate ChatGPT to replacement-list writes so its known writes
  validate before storage mutation. This proposal does not promise immutable
  snapshots or atomic multi-update transactions.

## Migration and session compatibility

1. Record owner approval of this recommendation and policy, or revise this
   document to the owner's chosen alternative. Do not start runtime work first.
2. Implement schema discovery, key checks, and the bounded validator in the
   existing `extensions/handlers/context_manager` package. Retain `BaseContext`,
   `BaseContextManager`, `props`, `ctx`, and `user_data` so handler inheritance
   and callback/message construction do not need a redesign.
3. Convert every writer/exclusion listed above in one runtime PR. Change
   ChatGPT to `list[str] | None`, replace history appends with validated setters,
   and update its cleanup override. There is no compatibility adapter for the
   old expression-based API, since such an adapter would retain stack inspection.
4. Replace the helper tests with explicit-key/schema tests and add the behavior
   checks below. Remove `Property`, `make_prop`, `make_args_names_list`,
   `uncast_opt`, and other obsolete helpers after all callers are gone.
5. Verify there are no remaining `varname` consumers, then remove its direct
   dependency and refresh `uv.lock` and generated requirement exports using the
   repository workflow. Do not manually remove transitive packages still needed
   by other dependencies.

Keep every stored key, FSM state string, middleware mapping, and nested-handler
handoff unchanged. Existing valid raw-list ChatGPT histories already containing
strings pass the new annotation. Histories containing other objects now fail
validation and require an explicit flow restart; do not silently drop or coerce
history. A fresh ChatGPT initialization clears invalid history and creates an
empty validated list. Other flow entrypoints similarly reset only their schema.

The production process currently loses both middleware data and FSM memory on a
restart, so a normal code deployment cannot preserve sessions across that restart.
For a retained mapping in tests or a future hot reload, the key/value layout is
compatible and must be covered by fixtures that prepopulate legacy dictionaries.
There is no durable context format or serializer introduced here. Future Redis
storage would need codecs for `Message`, date/time, and timedelta, plus a versioned
session migration. `Any` fields and shared flat keys remain compatibility debts.

The flat `"message"` key is shared by reminder and add-book flows. Per-user data
can also leak between chats; replacing keys does not fix that existing behavior.
The private-topics work should define mapping ownership using its approved
`bot/chat/user/message_thread_id` identity and inject the appropriate mapping
through the existing `user_data` contract. This manager must neither construct
that identity nor read it from stack frames. Draft/status/error thread routing
belongs to that downstream task. This proposal supplies no runtime prerequisite
until owner approval and a separate implementation are complete.

Rollback means deploying the old code, with the same restart-related session
loss. Valid new values use the old layout; the old API still needs its old
callers and `varname` dependency together. Do not mix old/new call signatures
within one deployment. Preserve `state.clear()` behavior and current FSM scope
in this replacement; coordinate any later storage change explicitly.

## Required checks for the runtime PR

- Preserve the seven existing manager behaviors, replacing expression arguments
  with strings. Give each test a fresh mapping so order cannot affect results.
- Verify keys passed through local variables and wrapper functions; test unknown
  set/exclusion keys, including a valid exclusion followed by an invalid one,
  with no partial mutation. A method on a schema must not become a data field.
- Test nullable writes, empty and populated `list[str]`, nested lists/dicts,
  both union spellings, wrong outer/element/key/value types, strict integers,
  `Any`, live `Message` identity/subclasses, and unsupported schema failures.
  Test both read and write paths and error messages without stored contents.
- Prepopulate each of the six contexts with its legacy key/value layout, then
  read, update, and clean it. Preserve unrelated sentinel keys and
  `delete_queue`; verify the reminder timezone exclusion and both book-edit
  exclusions. Confirm cleanup can recover an invalid old value.
- Exercise ChatGPT initialization and two answers with fresh validated lists,
  correct history order, and no raw-list annotation or direct append remaining.
- Exercise add-book completion, reminder completion, book callback-to-message
  editing, download filename use, and road-settings callback-to-message update
  with real handler context injection and mocked external I/O. Assert the same
  mapping reaches nested handlers and existing FSM transitions stay intact.
- Re-run `bot/tests/middlewares/test_downstream_results.py`,
  `bot/tests/middlewares/test_delete_queue.py`, and the full suite. Run lint on
  changed Python files and distinguish existing imported-module findings.

## Evidence for this documentation PR

- `uv sync --locked` created a local worktree environment without changing the
  lockfile. No root checkout or root `.env` was used.
- `make test FILE=bot/tests/contrib`: 8 passed, with two existing `varname`
  warnings about fallback evaluation.
- `make test`: 105 passed, 13 skipped, five existing warnings.
- `make lint FILE=bot/extensions/handlers/context_manager`: stopped at 13
  existing Ruff findings in unchanged code; later lint stages did not run.
  This documentation PR does not repair those findings.

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

Please explicitly approve the recommended explicit-key dataclass adapter,
validation policy, and preservation of the current storage boundary, or name an
alternative above. Approval is pending. Keep the task file until that decision
is recorded; this documentation PR alone does not complete its acceptance criteria.
