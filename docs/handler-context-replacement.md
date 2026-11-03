# Handler context fields

The handler context manager previously inspected caller stack frames with
`varname` to discover field names. It also compared values with annotations by
exact type identity, so an annotation such as `list[str]` did not work.

Each context now declares each field once. `ContextField[T]` is a descriptor:
access through the context class returns the typed field, while access through a
context instance returns the value. Python calls `__set_name__` when the class is
created to assign the storage key; handler calls do not inspect the stack.

```python
class DownloadContext(BaseContext):
    file_name = ContextField[str](str)

self.set(self.props.file_name, self.event.text)
filename = self.ctx.file_name
```

Each field is optional. A type checker can detect an unknown attribute or a value
that is incompatible with a field. `set` also rejects a field belonging to a
different context, validates the value, and stores it under the existing string
key. `ctx` validates values before returning a view. The view retains references
to stored objects; assigning an attribute changes only that view, just as with
the previous dataclass snapshot. In-place mutations of a stored list remain
visible, and are checked on the next `ctx` read.

The manager checks exact types for the existing scalar and `Message` fields,
accepts any value for `Any`, and checks every element of `list[str]`. Unsupported
field types raise `TypeError`; invalid values raise `ValueError` without including
the value. `clean_context` takes fields to preserve, checks them before mutation,
sets the other context fields to `None`, and leaves unrelated keys untouched.
This lets cleanup recover even when old values are invalid.

## Current consumers

Paths are relative to `bot/handlers/user/`. All fields allow `None`.

- `chatgpt/_context.py`: `messages` is `list[str]`. `init.py` initializes the
  list and `answer.py` appends the prompt and answer.
- `download/_context.py`: `file_name` is `str`. The init, get-name, and download
  handlers clear, write, and read it.
- `reminder/_context.py`: `text` is `str`, `tz` is `timedelta`, `date` and
  `time` are datetime types, and `message` is an aiogram `Message`. The start,
  input, create, and widget handlers use them. Cleanup preserves `tz`, which
  timezone middleware also supplies.
- `road/settings/_context.py`: `setting_name` is `str` and `setting_new_value`
  is `Any`. The callback writes the name; the message handler writes and saves
  the parsed value.
- `books/messages/add/_context.py`: `name` and `author` are `str`, `chapter_cnt`
  is `int`, and `message` is an aiogram `Message`. The start, input, create, and
  widget handlers share the context.
- `books/messages/edit_property/_context.py`: `property_name` and `new_value`
  are `str`, and `book_id` is `int`. The callback passes the mapping to the
  message handlers; cleanup preserves the selected book and property.

`delete_queue` is owned by middleware and is not a context field. Nested
handlers keep receiving the same user-data mapping. Direct aiogram FSM data users
are separate and do not use this manager.

## Storage and migration

The manager continues to use the flat per-user mapping from `UserDataMiddleware`,
not aiogram FSM data. The bot currently uses in-memory storage for both, so a
process restart loses in-progress sessions. Existing valid mapping values need no
conversion. A ChatGPT history containing a non-string now raises an error until
the user starts that flow again; it is not silently filtered.

The old shared `message` key and per-user rather than per-chat scope remain.
Private-topic isolation and routing are separate work. Existing callers must use
fields from `self.props`, not the intermediate enum or string API from earlier
versions of this PR.

## Alternatives

Dataclass serialization would copy values and does not enforce annotations.
Typed dictionaries provide static key checking but would change every attribute
read and still require runtime validation. Direct aiogram FSM data access is
asynchronous and has different storage, scoping, and clearing behavior. The
field descriptor preserves the existing access style and mapping while removing
stack inspection and duplicate field/key declarations.

The implementation was requested by the owner after reviewing the proposal.
