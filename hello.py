import aiogram
from bot_config import bot
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


async def start(message: aiogram.types.message):
    button_tasks = KeyboardButton('/add_row')
    button_log = KeyboardButton('/get_log')
    button_trash = KeyboardButton('/trash')
    greet_kb = ReplyKeyboardMarkup(resize_keyboard=True,
                                   one_time_keyboard=True,
                                   input_field_placeholder='Строка')
    greet_kb.add(button_tasks, button_trash, button_log)
    await message.answer('Приветствую тебя!')
    await message.answer('Чем займемся?', reply_markup=greet_kb)
