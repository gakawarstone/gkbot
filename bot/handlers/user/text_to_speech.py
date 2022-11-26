from io import BytesIO

import gtts
from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.state import State, StateFilter, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile

from ._commands import USER_COMMANDS


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


def setup(r: Router):
    r.message.register(start, StateFilter(FSM.start))
    r.message.register(msg_to_voice, StateFilter(FSM.msg_to_voice))
    r.message.register(start, Command(commands=USER_COMMANDS.tts))
