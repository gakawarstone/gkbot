from typing import Any

from models.books import Book


class BooksRepository:
    @classmethod
    async def get_all_user_books(cls, user_id: int) -> list[Book]:
        return await Book.filter(user_id=user_id).all()

    @classmethod
    async def get_book_by_id(cls, book_id: int) -> Book:
        return await Book.filter(id=book_id).first()

    @classmethod  # FIXME
    async def edit_book_property(
        cls, book_id: int, property_name: str, new_property_value: Any
    ):
        kwargs = {property_name: new_property_value}
        await Book.filter(id=book_id).update(**kwargs)

    @classmethod
    async def delete_book(cls, book: Book) -> None:
        await Book.filter(id=book.id).delete()

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
        await Book.filter(id=book.id).update(current_chapter=current_chapter)
