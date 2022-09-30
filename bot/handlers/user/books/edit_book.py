from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from models.books import Book
from services.books import BookService
from ui.keyboards.books import BookMarkup, BookEditMarkup
from .states import FSM

# [ ] add message folder


async def choose_book(message: Message):
    books = await BookService.get_all_user_books(message.from_user.id)
    markup = BookMarkup.get_books_dialog(BookMarkup.events.edit, books)
    await message.answer('Выберите книгу которую вы хотите обновить',
                         reply_markup=markup)


async def choose_property_to_edit(message: Message, book: Book):
    await message.answer(
        'Выберите поле которое вы бы хотели отредактировать',
        reply_markup=BookEditMarkup.get_edit_properties_dialog(book)
    )


async def init(message: Message, state: FSMContext, data: dict):
    text = f'Введите новое значение для {data["book_property_name"]}'
    await message.answer(text)
    await state.set_state(FSM.change_book_property)


async def change_book_property(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.finish)
    book_id = data['book_id']
    property_name = data['book_property_name']
    new_property_value = message.text
    await BookService.edit_book_property(
        book_id=book_id,
        property_name=property_name,
        new_property_value=new_property_value
    )
    # NOTE BookService.change_book_property(book, property_name)


def setup(r: Router):
    r.message.register(change_book_property, StateFilter(
        state=FSM.change_book_property))
