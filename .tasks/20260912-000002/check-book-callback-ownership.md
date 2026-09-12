# Check ownership in book callbacks

- STATUS: OPEN
- PRIORITY: 1

## Problem

Book callback handlers load a book by its numeric ID without checking `callback.from_user.id`. A user who can access another user's inline keyboard can show, edit, increment, decrement, or delete that user's book.

## Plan

1. Add a repository method that loads a book by both book ID and user ID.
2. Use the callback sender as the owner in every book callback path.
3. Return a clear callback response when the book does not exist or belongs to another user.
4. Add tests for an owner, another user, a missing book, and each mutating callback action.

## Acceptance criteria

- Book callback actions only operate on books owned by the callback sender.
- Forged or stale callback data cannot reveal or modify another user's book.
- The bot answers rejected callbacks without raising an unhandled exception.
- Focused repository and handler tests pass.

