from dataclasses import dataclass
from enum import Enum


@dataclass
class _BookProperty:
    name_in_db: str
    spell_ru: str
    event_code: str


class _BookProperties(Enum):
    NAME = _BookProperty(name_in_db="name", spell_ru="Название", event_code="ttl")
    AUTHOR = _BookProperty(name_in_db="author", spell_ru="Автор", event_code="aut")
    PROGRESS = _BookProperty(
        name_in_db="current_chapter", spell_ru="Прогресс", event_code="prg"
    )
    TOTAL_CHAPTERS = _BookProperty(
        name_in_db="chapters_cnt", spell_ru="Всего глав", event_code="tlc"
    )


# NOTE enum instead of dataclass
@dataclass
class _Buttons:
    add_new_book = "📘 Добавить"
    my_books = "📚 Мои книги"
    update_book = "✏️ Изменить"
    delete_book = "❌ Удалить"
    exit = "🚪 Выйти"


@dataclass
class _Events:
    show = "show"
    increment = "inc"
    decrement = "dec"
    edit = "edt"
    delete = "del"
