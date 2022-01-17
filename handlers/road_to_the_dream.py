import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

from bot_config import bot


async def start(message: aiogram.types.Message):
    await message.answer('Hello you start with productivity module')
    buttons = [['Pomodoro', 'Habit tracker']]
    bot.add_keyboard('road_choose', buttons)
    await message.answer('Please choose tool', reply_markup=bot.keyboards['road_choose'])
    print('after adding keyboard')
    bot.add_state_handler(FSM.choose_tool, choose_tool)
    await FSM.choose_tool.set()


async def choose_tool(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    if message.text == 'Pomodoro':
        await pomodoro(message)
    elif message.text == 'Habit tracker':
        await habit_tracker(message)


async def pomodoro(message: aiogram.types.Message):
    await message.answer('you start pomodoro')


async def habit_tracker(message: aiogram.types.Message):
    await message.answer('you start habit tracker')


class FSM(StatesGroup):
    init = State()
    choose_tool = State()
    pomodoro = State()
