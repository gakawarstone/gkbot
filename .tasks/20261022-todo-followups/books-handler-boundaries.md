# Validate book edits and move persistence behind the repository

- STATUS: OPEN
- PRIORITY: 3

## Problem

Three markers concern one unfinished flow. `CreateBookHandler` calls `Book.get_or_create` directly, `GetNewPropertyValueHandler` stores raw message text, and `BooksRepository.edit_book_property` accepts any field name and updates by book ID without the acting user's ID.

## Acceptance criteria

- Add a repository creation method and use it from the add-book handler, preserving duplicate-book behavior.
- Define the editable fields and parse numeric chapter values before updating the database.
- Reject non-text messages, unknown fields, invalid numbers, and chapter values outside the supported range with a useful response and a retryable FSM state.
- Require the acting user's ID when updating and reject missing or foreign books.
- Test successful edits, rejected values, and attempts to edit another user's book.

## Locations

- `bot/handlers/user/books/messages/add/create.py`
- `bot/handlers/user/books/messages/edit_property/get_new_value.py`
- `bot/services/repositories/books.py`
