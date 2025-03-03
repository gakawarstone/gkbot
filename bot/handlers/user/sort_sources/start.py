from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.static import Images
from ._states import FSM


async def init(message: Message, state: FSMContext):
    await message.delete()
    await state.set_state(FSM.sort_file)
    text = "Вы включили сортировщик призваный избавить вас от ручной работы "
    text += "<b>Отправьте .txt файл с вашими источниками</b>"
    await message.answer_photo(
        await Images.sort_documents.as_input_file(), caption=text
    )
