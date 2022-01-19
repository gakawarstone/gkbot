from datetime import datetime
from pprint import pprint

import asyncio
import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove

from bot_config import bot

data = {'pomodoro_cnt': 0,
        'msg_if_restart': None}


async def start(message: aiogram.types.Message):
    await message.answer('Привет _%s_ ты включил модуль 🚀*РОД ЗЕ ДРИМ*🚀' %
                         message['from']['first_name'])
    buttons = [['Помидор 🕔', 'Трекер привычек']]
    bot.add_keyboard('road_choose', buttons)
    await message.answer('Пожалуйста выберите 🛠 *инструмент*',
                         reply_markup=bot.keyboards['road_choose'])
    bot.add_state_handler(FSM.choose_tool, choose_tool)
    await FSM.choose_tool.set()


async def choose_tool(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    await message.delete()
    if message.text == 'Помидор 🕔':
        await pomodoro(message)
    elif message.text == 'Трекер привычек':
        await habit_tracker(message)


async def pomodoro(message: aiogram.types.Message,
                   time_focused: int = 15,
                   time_relax: int = 15):
    await message.answer('Вы включили 🕔 *помидор*',
                         reply_markup=ReplyKeyboardRemove())

    msg = await message.answer('У вас _15_ минут *будьте сконцентрированы*')
    await timer(message['from']['id'], time_focused, text='_Вжаривай по полной_')

    await msg.edit_text('Теперь у вас есть время на отдых _15 минут_')
    await timer(message['from']['id'], time_relax, text='_На чиле_')

    data['pomodoro_cnt'] += 1
    await msg.edit_text('*Поздравляю* вы получили %s' % ('🍅' * data['pomodoro_cnt']))

    bot.add_keyboard('choose_bool', [['Да', 'Нет']])
    data['msg_if_restart'] = await message.answer('Хотите начать новый помидор?',
                                                  reply_markup=bot.keyboards['choose_bool'])
    bot.add_state_handler(FSM.choose_bool, choose_bool)
    await FSM.choose_bool.set()


async def choose_bool(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    if message.text == 'Да':
        await pomodoro(message)
    else:
        assert message.text == 'Нет'
        pass


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
                                remain_time).strftime(format))
        await asyncio.sleep(delay)
    await msg.delete()


async def habit_tracker(message: aiogram.types.Message):
    await message.answer('Вы включили трекер привычек', reply_markup=ReplyKeyboardRemove())
    await message.answer('Ты хули сюда залез невидишь что нет ничего')


class FSM(StatesGroup):
    init = State()
    choose_tool = State()
    pomodoro = State()
    choose_bool = State()
