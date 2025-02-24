from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery

from services.ytdlp import YtdlpDownloader
from ui.keyboards.ytdlp import YtdlpMarkup

F: CallbackQuery


async def delete_download_markup(callback: CallbackQuery):
    await callback.message.delete()


async def download_audio(callback: CallbackQuery, bot: Bot):
    request_from_user_id = int(callback.data.split(":")[1])
    if callback.from_user.id != request_from_user_id:
        return

    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=callback.data.split(":")[2]
    )
    await callback.message.edit_reply_markup()
    await callback.message.edit_text("Cкачиваю " + (url := callback.message.text))
    audio = await YtdlpDownloader.download_audio(url)
    await callback.message.answer_audio(
        audio=audio.input_file,
        title=audio.title,
        performer="GKBOT",
        duration=audio.duration,
    )
    await callback.message.delete()


async def download_video(callback: CallbackQuery, bot: Bot):
    request_from_user_id = int(callback.data.split(":")[1])
    if callback.from_user.id != request_from_user_id:
        return

    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=callback.data.split(":")[2]
    )
    await callback.message.edit_reply_markup()
    await callback.message.edit_text("Cкачиваю " + (url := callback.message.text))
    video_file = await YtdlpDownloader.download_video(url)
    await callback.message.answer_video(video_file)
    await callback.message.delete()


def setup(r: Router):
    r.callback_query.register(
        delete_download_markup, F.data.startswith(YtdlpMarkup.data.delete)
    )
    r.callback_query.register(download_audio, F.data.startswith(YtdlpMarkup.data.mp3))
    r.callback_query.register(download_video, F.data.startswith(YtdlpMarkup.data.mp4))
