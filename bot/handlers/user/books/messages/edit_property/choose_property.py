from aiogram.types import Message

from models.books import Book
from ui.keyboards.books import PropertiesMarkup


async def choose_property_to_edit(message: Message, book: Book):
    await message.delete()
    await message.answer(
        'Выберите поле которое вы бы хотели отредактировать',
        reply_markup=PropertiesMarkup.get_edit_properties_dialog(book)
    )
