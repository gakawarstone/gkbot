from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from services.youtube import YouTubeDownloader
from ui.keyboards.youtube import YouTubeMarkup

F: CallbackQuery


async def delete_download_markup(callback: CallbackQuery):
    await callback.message.delete()


async def download_audio(callback: CallbackQuery, state: FSMContext):
    request_from_user_id = int(callback.data.split(':')[1])
    if callback.from_user.id != request_from_user_id:
        return

    await state.bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.data.split(':')[2]
    )
    await callback.message.edit_reply_markup()
    await callback.message.edit_text('Cкачиваю ' +
                                     (url := callback.message.text))
    audio = await YouTubeDownloader.download_audio(url)
    await callback.message.answer_audio(
        audio=audio.input_file,
        title=audio.title,
        performer='GKBOT',
        duration=audio.duration
    )
    await callback.message.delete()


def setup(r: Router):
    r.callback_query.register(
        delete_download_markup,
        F.data.startswith(YouTubeMarkup.data.delete)
    )
    r.callback_query.register(
        download_audio,
        F.data.startswith(YouTubeMarkup.data.mp3)
    )