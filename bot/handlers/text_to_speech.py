import io

from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.fsm.context import FSMContext
import gtts

from settings import bot


class FSM(StatesGroup):
    start = State()
    msg_to_voice = State()


@bot.dp.message(commands='tts', state=FSM.start)
async def start(message: Message, state: FSMContext):
    await state.set_state(FSM.msg_to_voice)
    await message.answer('Привет это новая функция сделанная потомучто <b>могу</b>')
    await message.answer('Отправь мне сообщение и произойдет магия')


@bot.dp.message(state=FSM.msg_to_voice)
async def msg_to_voice(message: Message, state: FSMContext):
    voice_file = io.BytesIO()
    voice = gtts.gTTS(text=message.text, lang='ru')
    voice.write_to_fp(voice_file)
    await message.answer_audio(BufferedInputFile(voice_file.getvalue(), 'a.mp3'), title='Текст')
