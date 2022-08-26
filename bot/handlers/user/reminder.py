from datetime import datetime, date, timedelta, time

from aiogram.types import Message
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message
from lib.bot import BotManager

from services.reminder import Reminder
from ui.keyboards.reminder import RemindMarkup
from ui.components.remind_creator import RemindCreator


# [ ] add menu set repeatable notifications


class FSM(StatesGroup):
    add = State()
    get_remind_text = State()
    get_remind_date = State()
    get_remind_time = State()
    finish = State()


async def add(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.get_remind_text)
    await message.delete()
    data['rc'] = RemindCreator(message.chat.id)
    await data['rc'].init()


async def get_remind_text(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.get_remind_date)
    await message.delete()
    data['text'] = message.text

    rc: RemindCreator = data['rc']
    await rc.set_remind_text(message.text)

    data['mes_date'] = await message.answer('Выберите дату',
                                            reply_markup=RemindMarkup.date)


async def get_remind_date(message: Message, state: FSMContext, data: dict):
    await message.delete()
    await data['mes_date'].delete()
    rc: RemindCreator = data['rc']
    try:
        await state.set_state(FSM.get_remind_time)
        data['date'] = validate_date(message.text)
        await rc.set_remind_date(data['date'].strftime('%d.%m.%Y'))
    except(Exception):
        await state.set_state(FSM.get_remind_date)
        await rc.set_status_message('❌<b>Формат [30.12.2021]</b>❌')
        data['mes_date'] = await data['mes_date'].send_copy(
            message.chat.id, reply_markup=RemindMarkup.date())


def validate_date(text: str) -> datetime:  # FIXME move
    match text:
        case RemindMarkup.buttons.today | '1':
            return date.today()
        case RemindMarkup.buttons.tomorrow | '2':
            return date.today() + timedelta(days=1)
        case _:
            return datetime.strptime(text, '%d.%m.%Y')


async def get_remind_time(message: Message, state: FSMContext, data: dict):
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
