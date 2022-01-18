from datetime import datetime
from pprint import pprint

import asyncio
import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, ParseMode

from bot_config import bot


async def start(message: aiogram.types.Message):
    await message.answer('Привет _%s_ ты включил модуль 🚀*РОД ЗЕ ДРИМ*🚀' %
                         message['from']['first_name'],
                         parse_mode=ParseMode.MARKDOWN)
    buttons = [['Помидор', 'Трекер привычек']]
    bot.add_keyboard('road_choose', buttons)
    await message.answer('Пожалуйста выберите *инструмент*',
                         reply_markup=bot.keyboards['road_choose'],
                         parse_mode=ParseMode.MARKDOWN)
    bot.add_state_handler(FSM.choose_tool, choose_tool)
    await FSM.choose_tool.set()


async def choose_tool(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    await message.delete()
    if message.text == 'Помидор':
        await pomodoro(message)
    elif message.text == 'Трекер привычек':
        await habit_tracker(message)


async def pomodoro(message: aiogram.types.Message,
                   time_focused: int = 15,
                   time_relax: int = 15):
    await message.answer('Вы включили *помидор*',
                         reply_markup=ReplyKeyboardRemove(),
                         parse_mode=ParseMode.MARKDOWN)

    msg = await message.answer('У вас _15_ минут *будьте сконцентрированы*',
                               parse_mode=ParseMode.MARKDOWN)
    await timer(message['from']['id'], time_focused, text='_[Вжаривай по полной]_')

    await msg.edit_text('Теперь у вас есть время на отдых _[15 минут]_',
                        parse_mode=ParseMode.MARKDOWN)
    await timer(message['from']['id'], time_relax, text='_[На чиле]_')

    await msg.edit_text('*Поздравляю* вы получили 🍅',
                        parse_mode=ParseMode.MARKDOWN)


async def timer(chat_id: str, seconds: int,
                text: str = 'Start', delay: int = 1,
                format: str = '%M:%S'):
    msg = await bot.send_message(chat_id, text)
    now = datetime.now().timestamp()
    finish_time = now + seconds
    while True:
        now = datetime.now().timestamp()
        remain_time = finish_time - now
        if now >= finish_time:
            break
        await msg.edit_text(text + ' *%s*' %
                            datetime.fromtimestamp(
                                remain_time).strftime(format),
                            parse_mode=ParseMode.MARKDOWN)
        await asyncio.sleep(delay)
    await msg.delete()


async def habit_tracker(message: aiogram.types.Message):
    await message.answer('Вы включили трекер привычек', reply_markup=ReplyKeyboardRemove())
    await message.answer('Ты хули сюда залез невидишь что нет ничего')


class FSM(StatesGroup):
    init = State()
    choose_tool = State()
    pomodoro = State()
    finish = State()
