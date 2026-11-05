from models.books import Book


class BooksRepository:
    @classmethod
    async def get_all_user_books(cls, user_id: int) -> list[Book]:
        return await Book.filter(user_id=user_id).all()

    @classmethod
    async def get_user_book_by_id(cls, book_id: int, user_id: int) -> Book:
        book = await Book.filter(id=book_id, user_id=user_id).first()
        if book is None:
            raise ValueError(
                f"Book with id={book_id} not found for user with id={user_id}"
            )
        return book

    @classmethod
    async def edit_book_property(
        cls,
        book_id: int,
        user_id: int,
        property_name: str,
        new_property_value: str | None,
    ) -> None:
        if property_name not in {"name", "author", "current_chapter", "chapters_cnt"}:
            raise ValueError("Это поле нельзя изменить")
        if not new_property_value or not new_property_value.strip():
            raise ValueError("Введите непустое текстовое значение")

        value: str | int = new_property_value.strip()
        query = Book.filter(id=book_id, user_id=user_id)
        if property_name in {"current_chapter", "chapters_cnt"}:
            try:
                value = int(value)
            except ValueError as exc:
                raise ValueError("Введите целое число") from exc
            if not 0 <= value <= 2147483647:
                raise ValueError("Введите число глав от 0 до 2147483647")
            if property_name == "current_chapter":
                query = query.filter(chapters_cnt__gte=value)
            else:
                query = query.filter(current_chapter__lte=value)

        if not await query.update(**{property_name: value}):
            raise ValueError("Книга не найдена или прогресс превышает число глав")

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
