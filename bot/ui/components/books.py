from models.books import Book


class BookComponent:
    @classmethod
    def render(cls, book: Book):  # FIXME style
        text = f'<b>Название ✍️:</b>                 {book.name}\n'
        text += f'<b>Автор 👨‍🦳:</b>                         {book.author}\n'
        text += f'<b>Прогресс(главы) 📈:</b>     <b>{book.current_chapter}</b> из {book.chapters_cnt}'
        return text
