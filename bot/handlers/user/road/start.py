from aiogram import Router
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from settings import logger
from ui.keyboards.road import RoadMarkup
from .states import FSM


# [ ] move to menu?


async def start(message: Message, state: FSMContext):
    await state.set_state(FSM.choose_tool)
    logger.debug('Road handler started')
    photo_id = 'AgACAgIAAxkDAALtVWHn3ZZmzpMfA3SI7usT1avw9xrWAALRtjEbe9FASzJZxPBxsVhdAQADAgADeQADIwQ'
    logger.warning(
        'Make sure that bot can use this photo_id: ' + photo_id)  # BUG
    await message.answer_photo(
        photo_id,
        caption='Привет <i>%s</i> ты включил модуль 🚀<b>РОД ЗЕ ДРИМ</b>🚀' %
                message.from_user.first_name)
    await message.answer('Пожалуйста выберите 🛠 <b>инструмент</b>',
                         reply_markup=RoadMarkup.tools)


def setup(r: Router):
    r.message.register(start,
                       StateFilter(state=FSM.start) | Command(commands='road'))
