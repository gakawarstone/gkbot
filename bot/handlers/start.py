from aiogram.types import Message

from settings import mng

# [ ] delete(move to menu)


async def start(message: Message):
    commands = [['/add_row', '/trash', '/bomber'],
                ['/get_log', '/get_trash']]
    bot.add_keyboard('all_commands', commands, placeholder='Выберите команду')
    await message.answer('Приветствую тебя!')
    await message.answer('Чем займемся?',
                         reply_markup=bot.keyboards['all_commands'])
