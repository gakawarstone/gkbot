import aiogram

from bot_config import bot


async def start(message: aiogram.types.message):
    commands = [['/add_row', '/trash', '/bomber'],
                ['/get_log', '/get_trash']]
    bot.add_keyboard('all_commands', commands)
    await message.answer('Приветствую тебя!')
    await message.answer('Чем займемся?',
                         reply_markup=bot.keyboards['all_commands'])
