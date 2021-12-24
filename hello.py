import aiogram
from bot_config import bot


async def start(message: aiogram.types.message):
    bot.add_keyboard('all_commands', ['/add_row',
                                      '/get_log',
                                      '/trash',
                                      '/get_trash'])
    await message.answer('Приветствую тебя!')
    await message.answer('Чем займемся?',
                         reply_markup=bot.keyboards['all_commands'])
