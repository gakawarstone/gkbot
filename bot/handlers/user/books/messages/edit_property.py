from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from models.books import Book
from services.books import BookService
from ui.keyboards.books import EventsMarkup, PropertiesMarkup
from ..states import FSM


async def choose_book(message: Message):
    books = await BookService.get_all_user_books(message.from_user.id)
    markup = EventsMarkup.get_books_dialog(EventsMarkup.events.edit, books)
    await message.answer('Выберите книгу которую вы хотите обновить',
                         reply_markup=markup)


async def choose_property_to_edit(message: Message, book: Book):
    await message.delete()
    await message.answer(
        'Выберите поле которое вы бы хотели отредактировать',
        reply_markup=PropertiesMarkup.get_edit_properties_dialog(book)
    )


async def init(message: Message, state: FSMContext, data: dict):
    text = f'Введите новое значение для {data["book_property_name"]}'
    await message.answer(text)
    await state.set_state(FSM.change_book_property)


async def change_book_property(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.check_menu_command)
    await message.delete()
    try:
        await BookService.edit_book_property(
            book_id=data['book_id'],
            property_name=data['book_property_name'],
            new_property_value=message.text
        )
        await message.answer('Успешно изменено')
    except:  # FIXME bare exception
        await message.answer('Что то пошло не так')


def setup(r: Router):
    r.message.register(change_book_property, StateFilter(
        state=FSM.change_book_property))
