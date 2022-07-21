from io import BytesIO

from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.fsm.context import FSMContext
import gtts

from lib.bot import BotManager


class FSM(StatesGroup):
    start = State()
    msg_to_voice = State()
    finish = State()


async def start(message: Message, state: FSMContext):
    await state.set_state(FSM.msg_to_voice)
    await message.answer('Привет это новая функция сделанная потомучто <b>могу</b>')
    await message.answer('Отправь мне сообщение и произойдет магия')


async def msg_to_voice(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    gtts.gTTS(text=message.text, lang='ru').write_to_fp(
        voice_file := BytesIO())
    await message.answer_audio(BufferedInputFile(voice_file.getvalue(),
                                                 'a.mp3'), title='Текст')


def setup(mng: BotManager):
    mng.add_state_handler(FSM.start, start)
    mng.add_state_handler(FSM.msg_to_voice, msg_to_voice)
