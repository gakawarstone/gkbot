from aiogram.types import Message

from ui.keyboards import StartMarkup

# [ ] delete(move to menu)


async def start(message: Message):
    await message.answer('Приветствую тебя!')
    await message.answer('Чем займемся?',
                         reply_markup=StartMarkup.commands())
