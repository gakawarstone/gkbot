from typing import Any
from sqlalchemy import select, delete, update
from configs import db
from models.books import Book


class BooksRepository:
    @classmethod
    async def get_all_user_books(cls, user_id: int) -> list[Book]:
        async with db.SessionLocal() as session:
            stmt = select(Book).where(Book.user_id == user_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @classmethod
    async def get_book_by_id(cls, book_id: int) -> Book:
        async with db.SessionLocal() as session:
            stmt = select(Book).where(Book.id == book_id)
            result = await session.execute(stmt)
            book = result.scalar_one_or_none()
            if book is None:
                raise ValueError(f"Book with id={book_id} not found")
            return book

    @classmethod
    async def edit_book_property(
        cls, book_id: int, property_name: str, new_property_value: Any
    ):
        async with db.SessionLocal() as session:
            stmt = update(Book).where(Book.id == book_id).values({property_name: new_property_value})
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def delete_book(cls, book: Book) -> None:
        async with db.SessionLocal() as session:
            stmt = delete(Book).where(Book.id == book.id)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def increment_book_current_chapter(cls, book: Book) -> Book:
        if book.current_chapter < book.chapters_cnt:
            book.current_chapter += 1
            await cls.__update_book_current_chapter(book, book.current_chapter)
        return book

    @classmethod
    async def decrement_book_current_chapter(cls, book: Book) -> Book:
        if book.current_chapter > 0:
            book.current_chapter -= 1
            await cls.__update_book_current_chapter(book, book.current_chapter)
        return book

    @classmethod
    async def __update_book_current_chapter(
        cls, book: Book, current_chapter: int
    ) -> None:
        async with db.SessionLocal() as session:
            stmt = update(Book).where(Book.id == book.id).values(current_chapter=current_chapter)
            await session.execute(stmt)
            await session.commit()
