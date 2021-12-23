import aiogram
from bot_config import bot
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


async def start(message: aiogram.types.message):
    bot.add_keyboard('all_commands', ['/add_row',
                                      '/get_log',
                                      '/trash'])
    await message.answer('Приветствую тебя!')
    await message.answer('Чем займемся?',
                         reply_markup=bot.keyboards['all_commands'])
