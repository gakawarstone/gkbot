import pytest

from configs import db
from models.books import Book
from services.repositories.books import BooksRepository
from tests.mocks.db import use_db


async def add_book() -> None:
    async with db.SessionLocal() as session:
        session.add(
            Book(
                id=7,
                name="Dune",
                author="Frank Herbert",
                chapters_cnt=22,
                user_id=10,
            )
        )
        await session.commit()


@pytest.mark.asyncio
@use_db
async def test_get_user_book_by_id_checks_owner() -> None:
    await add_book()

    found_book = await BooksRepository.get_user_book_by_id(7, user_id=10)

    assert found_book.id == 7
    assert found_book.user_id == 10
    assert found_book.name == "Dune"


@pytest.mark.asyncio
@pytest.mark.parametrize("book_id, user_id", [(7, 11), (8, 10)])
@use_db
async def test_get_user_book_by_id_rejects_missing_or_foreign_book(
    book_id: int, user_id: int
) -> None:
    await add_book()

    with pytest.raises(ValueError, match="not found for user"):
        await BooksRepository.get_user_book_by_id(book_id, user_id)
