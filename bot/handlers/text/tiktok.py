from aiogram import F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message


from lib.bot import BotManager
from services.tiktok import TikTokDownloader, TikTokInvalidUrl
from filters.tiktok import TikTokVideoLink


F: Message


async def download_video(message: Message, state: FSMContext):
    status_message = await message.answer('Скачиваю %s' % message.text)
    await message.delete()
    await state.bot.send_chat_action(message.chat.id, 'upload_video')
    try:
        await message.answer_video(
            TikTokDownloader.get_video_url(message.text),
            caption=message.text
        )
    except TikTokInvalidUrl:
        await message.answer('Не получилось скачать %s' % message.text)
    await status_message.delete()


def setup(mng: BotManager):
    mng.dp.register_message(
        download_video,
        TikTokVideoLink()
    )
