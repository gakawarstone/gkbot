from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ._states import FSM


async def init(message: Message, state: FSMContext):
    await state.set_state(FSM.convert)
    text = 'Вы включили конвертер призваный избавить вас от ручной работы '
    text += '<b>Отправьте .docx файл</b>'
    await message.answer(text)
