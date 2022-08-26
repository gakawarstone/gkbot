from aiogram.types import Message

# [ ] delete(move to menu)


async def start(message: Message):
    await message.answer('Приветствую тебя!')
    await message.answer('Чем займемся?')
