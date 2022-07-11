from datetime import datetime, date, timedelta, time

from aiogram.types import Message
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message
from lib.bot import BotManager

from settings import mng  # FIXME
from services.reminder import Remind, Reminder
from components.remind_creator import RemindCreator

# [ ] add menu set repeatable notifications
# [ ] data middleware refactor to aiogram 3

data = {}  # FIXME middleware


class FSM(StatesGroup):
    add = State()
    get_remind_text = State()
    get_remind_date = State()
    get_remind_time = State()
    finish = State()


async def add(message: Message, state: FSMContext):
    await state.set_state(FSM.get_remind_text)
    await message.delete()
    remind_creator = RemindCreator(message.chat.id)
    data['rc'] = remind_creator

    await remind_creator.init()


async def get_remind_text(message: Message, state: FSMContext):
    await state.set_state(FSM.get_remind_date)
    await message.delete()
    data['text'] = message.text
    remind_creator: RemindCreator = data['rc']

    await remind_creator.set_remind_text(message.text)

    mng.add_keyboard('date', [['Сегодня', 'Завтра']],
                     placeholder='04.07.2022')
    data['mes_date'] = await message.answer('Выберите дату',
                                            reply_markup=mng.keyboards['date'])


async def get_remind_date(message: Message, state: FSMContext):
    try:
        await state.set_state(FSM.get_remind_time)
        await message.delete()
        await data['mes_date'].delete()
        remind_text = data['text']
        remind_creator: RemindCreator = data['rc']

        match message.text:
            case 'Сегодня' | '1':
                remind_date = date.today()
            case 'Завтра' | '2':
                remind_date = date.today() + timedelta(days=1)
            case _:
                remind_date = datetime.strptime(message.text, '%d.%m.%Y')
        data['date'] = remind_date

        await remind_creator.set_remind_date(remind_date.strftime('%d.%m.%Y'))

    except(Exception):
        await state.set_state(FSM.get_remind_date)
        await remind_creator.set_status_message(
            '❌<b>Формат [30.12.2021]</b>❌')
        data['mes_date'] = await message.answer(
            'Выберите дату', reply_markup=bot.keyboards['date'])


async def get_remind_time(message: Message, state: FSMContext):
    try:
        await state.set_state(FSM.finish)
        await message.delete()
        remind_creator: RemindCreator = data['rc']

        remind_time = time(*map(int, message.text.split(':')))
        Reminder.add_remind(message.from_user.id,
                            datetime.combine(data['date'], remind_time),
                            data['text'])

        await remind_creator.set_remind_time(remind_time.strftime('%H:%M'))
        await remind_creator.set_status_finished()
    except:
        await state.set_state(FSM.get_remind_time)
        await remind_creator.set_status_message('❌<b>Формат [10:14]</b>❌')


def setup(mng: BotManager):
    mng.add_state_handler(FSM.add, add)
    mng.add_state_handler(FSM.get_remind_date, get_remind_date)
    mng.add_state_handler(FSM.get_remind_text, get_remind_text)
    mng.add_state_handler(FSM.get_remind_time, get_remind_time)
