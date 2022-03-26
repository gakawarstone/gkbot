import aiogram

from . import users


async def help(message: aiogram.types.Message):
    text = 'Привет вот список команд которые есть в боте:\n\n'
    for cmd in users:
        text += '/%s\n' % cmd
    await message.answer(text)