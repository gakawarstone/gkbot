from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.books import Book
from services.repositories.books import BooksRepository


@pytest.mark.asyncio
async def test_get_user_book_by_id_checks_owner() -> None:
    book = Book(
        id=7,
        name="Dune",
        author="Frank Herbert",
        chapters_cnt=22,
        user_id=10,
    )
    query = MagicMock()
    query.first = AsyncMock(return_value=book)

    with patch.object(Book, "filter", return_value=query) as filter_books:
        found_book = await BooksRepository.get_user_book_by_id(7, user_id=10)

    assert found_book is book
    filter_books.assert_called_once_with(id=7, user_id=10)


@pytest.mark.asyncio
async def test_get_user_book_by_id_rejects_missing_or_foreign_book() -> None:
    query = MagicMock()
    query.first = AsyncMock(return_value=None)

    with (
        patch.object(Book, "filter", return_value=query) as filter_books,
        pytest.raises(ValueError),
    ):
        await BooksRepository.get_user_book_by_id(7, user_id=11)

    filter_books.assert_called_once_with(id=7, user_id=11)
