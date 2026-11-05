import pytest

from models.books import Book
from services.repositories.books import BooksRepository
from tests.mocks.db import use_db


@pytest.mark.asyncio
@use_db
async def test_edit_book_validates_and_isolates_owner():
    book = await Book.create(
        name="Book", author="Author", chapters_cnt=10, current_chapter=3, user_id=1
    )
    for field, value, user_id in [
        ("name", "Stolen", 2),
        ("user_id", "2", 1),
        ("name", "  ", 1),
        ("author", None, 1),
        ("current_chapter", "abc", 1),
        ("current_chapter", "-1", 1),
        ("current_chapter", "11", 1),
        ("chapters_cnt", "2", 1),
        ("chapters_cnt", "999999999999999999999", 1),
    ]:
        with pytest.raises(ValueError):
            await BooksRepository.edit_book_property(book.id, user_id, field, value)
    await book.refresh_from_db()
    assert (
        book.name,
        book.author,
        book.current_chapter,
        book.chapters_cnt,
        book.user_id,
    ) == ("Book", "Author", 3, 10, 1)
    await BooksRepository.edit_book_property(book.id, 1, "current_chapter", "10")
    await BooksRepository.edit_book_property(book.id, 1, "name", " New name ")
    await book.refresh_from_db()
    assert (book.name, book.current_chapter) == ("New name", 10)


@pytest.mark.asyncio
@use_db
async def test_invalid_edit_keeps_state_for_retry():
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, call

    from handlers.user.books.messages.edit_property._states import FSM as EditFSM
    from handlers.user.books.messages.edit_property.get_new_value import (
        GetNewPropertyValueHandler,
    )
    from handlers.user.books.states import FSM

    book = await Book.create(name="Book", author="Author", chapters_cnt=10, user_id=1)
    event = SimpleNamespace(
        from_user=SimpleNamespace(id=1), text="bad", answer=AsyncMock()
    )
    state = SimpleNamespace(set_state=AsyncMock())
    data = {"book_id": book.id, "property_name": "current_chapter"}
    await GetNewPropertyValueHandler(event, state=state, data=data).handle()
    assert state.set_state.await_args_list == [
        call(EditFSM.finish),
        call(FSM.finish),
        call(EditFSM.get_new_value),
    ]
    event.answer.assert_awaited_once_with("Введите целое число")
    assert data["book_id"] == book.id
    assert data["property_name"] == "current_chapter"
