from models.books import Book


class BookComponent:
    @classmethod
    def render(cls, book: Book) -> str:
        text = f'✍ Название :: {book.name}\n\n'
        text += f'👨‍🦳 Автор :: {book.author}\n\n'
        text += '📈 Прогресс(главы) :: '
        text += f'<b>{book.current_chapter}</b> из {book.chapters_cnt}'
        return text
