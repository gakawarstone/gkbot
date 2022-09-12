from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from ui.keyboards.books import BookMarkup
from ui.components.books import BookComponent
from models.books import Book
from .states import FSM

F: CallbackQuery


async def handle_book_events(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSM.check_menu_command)
    _, event, book_id = callback.data.split(':')
    book = await Book.filter(id=book_id).first()

    match event:
        case BookMarkup.events.increment:
            if book.current_chapter < book.chapters_cnt:
                book.current_chapter += 1
        case BookMarkup.events.decrement:
            if book.current_chapter > 0:
                book.current_chapter -= 1

    text = BookComponent.render(book)
    markup = BookMarkup.get_book_dialog(book)

    if event == BookMarkup.events.show:
        await callback.message.answer(text, reply_markup=markup)
    else:
        await Book.filter(id=book_id).update(
            current_chapter=book.current_chapter)

        await callback.message.edit_text(text, reply_markup=markup)


def setup(r: Router):
    r.callback_query.register(
        handle_book_events,
        F.data.startswith('book')
    )
