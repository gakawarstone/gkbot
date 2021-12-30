from bot_config import bot
import datetime
import aiogram
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
data = []


async def init(message: aiogram.types.Message):
    await message.answer('Вы хотите создать напоминание')
    await message.answer('Напоминание придет в этот чат в указанное время')
    await message.answer('Отправьте текст напоминания')
    bot.add_state_handler(FSM.get_mes, get_mes)
    await FSM.get_mes.set()


async def get_mes(message: aiogram.types.Message, state: FSMContext):
    data.append({
        'user': {
            'id': message['from']['id'],
            'name': message['from']['username']
        },
        'message': message.text
    })
    print(*data)
    await message.answer('Добавлено')


class FSM(StatesGroup):
    get_mes = State()
    get_time = State()


if __name__ == '__main__':
    bot.add_command_handler('remind', init)
    bot.start()
