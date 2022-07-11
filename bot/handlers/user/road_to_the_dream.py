import asyncio
from datetime import datetime
import logging

from aiogram.types import Message
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from lib.bot import BotManager

from settings import mng, Session  # FIXME
from models.road import Habits, PomodoroStats

logger = logging.getLogger(__name__)

logger.warning('Possible race condition')
data = {'msg_if_restart': None}


class FSM(StatesGroup):
    start = State()
    choose_tool = State()
    pomodoro = State()
    choose_bool = State()
    get_habit_name = State()
    get_habit_notify_time = State()
    finish = State()

# [ ] if road is already running do not start another


async def start(message: Message, state: FSMContext):
    await state.set_state(FSM.choose_tool)
    logger.debug('Road handler started')
    photo_id = 'AgACAgIAAxkDAALtVWHn3ZZmzpMfA3SI7usT1avw9xrWAALRtjEbe9FASzJZxPBxsVhdAQADAgADeQADIwQ'
    logger.warning('Make sure that bot can use this photo_id: ' + photo_id)
    await message.answer_photo(
        photo_id,
        caption='Привет <i>%s</i> ты включил модуль 🚀<b>РОД ЗЕ ДРИМ</b>🚀' %
        message.from_user.first_name)
    buttons = [['Помидор 🕔', 'Трекер привычек']]
    mng.add_keyboard('road_choose', buttons)
    await message.answer('Пожалуйста выберите 🛠 <b>инструмент</b>',
                         reply_markup=mng.keyboards['road_choose'])


async def choose_tool(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    await message.delete()
    match message.text:
        case 'Помидор 🕔' | '1':
            await pomodoro(message, state)
        case 'Трекер привычек' | '2':
            await habit_tracker(message, state)


async def pomodoro(message: Message, state: FSMContext,
                   time_focused: int = 15*60,
                   time_relax: int = 15*60):  # [ ] component
    await message.answer(
        'Вы включили 🕔 <b>помидор</b>',
        reply_markup=ReplyKeyboardRemove())

    msg = await message.answer(
        'У вас <i>15</i> минут <b>будьте сконцентрированы</b>')
    await timer(
        message.from_user.id,
        time_focused,
        text='<i>Вжаривай по полной</i>')

    await msg.edit_text('Теперь у вас есть время на отдых <i>15 минут</i>')
    await timer(
        message.from_user.id,
        time_relax,
        text='<i>На чиле</i>')

    with Session.begin() as session:
        user = session.query(
            PomodoroStats).filter_by(
            user_id=message.from_user.id).first()
        user.today_cnt += 1
        cnt = user.today_cnt
    await msg.edit_text(
        '<b>Поздравляю</b> вы получили <b>[<i>%s</i>🍅]</b>' % cnt)

    mng.add_keyboard('choose_bool', [['Да', 'Нет']])
    data['msg_if_restart'] = await message.answer(
        'Хотите начать новый помидор?',
        reply_markup=mng.keyboards['choose_bool'])

    await state.set_state(FSM.choose_bool)


async def choose_bool(message: Message):  # [ ] component
    await message.delete()
    assert data['msg_if_restart'] is not None
    await data['msg_if_restart'].delete()
    match message.text:
        case 'Да' | 'y':
            await pomodoro(message)
        case 'нет' | 'n':
            pass


async def timer(chat_id: str, seconds: int,
                text: str = 'Start', delay: int = 1,
                format_: str = '%M:%S'):  # [ ] component
    msg = await mng.send_message(chat_id, text)  # [ ]
    now = datetime.now().timestamp()
    finish_time = now + seconds
    while True:
        now = datetime.now().timestamp()
        remain_time = finish_time - now
        if now >= finish_time:
            break
        await msg.edit_text(text + ' <b>%s</b>' %
                            datetime.fromtimestamp(
                                remain_time).strftime(format_))
        await asyncio.sleep(delay)
    await msg.delete()


async def habit_tracker(message: Message, state: FSMContext):
    await state.set_state(FSM.get_habit_name)
    await message.answer(
        'Вы включили трекер привычек',
        reply_markup=ReplyKeyboardRemove())
    await message.answer('<b>Поздравляю</b> вы получили 🦣')
    await message.answer('Ладно заскамленное животное давай попробуем добавить привычку')
    await message.answer('Пришли мне название привычки которую мы с тобой будем прививать')


async def get_habit_name(message: Message, state: FSMContext):
    await state.set_state(FSM.get_habit_notify_time)
    data['habit_name'] = message.text
    await message.answer('Теперь пришли время в которое я буду спрашивать тебя об успехах')


async def get_habit_notify_time(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    time = datetime.strptime(message.text, '%H:%M').time()
    data['habit_notify_time'] = time
    with Session.begin() as session:
        habit = Habits(
            user_id=message.from_user.id,
            name=data['habit_name'],
            notify_time=data['habit_notify_time'])
        session.add(habit)
    await message.answer('Привычка добавлена')


def setup(mng: BotManager):
    mng.add_state_handler(FSM.start, start)
    mng.add_state_handler(FSM.choose_tool, choose_tool)
    mng.add_state_handler(FSM.choose_bool, choose_bool)
    mng.add_state_handler(FSM.pomodoro, pomodoro)
    mng.add_state_handler(FSM.get_habit_name, get_habit_name)
    mng.add_state_handler(FSM.get_habit_notify_time, get_habit_notify_time)
