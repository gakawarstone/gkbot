from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from services.tiktok import TikTokDownloader
from services.tiktok.exceptions import TikTokInvalidUrl, TikTokDownloadFailed
from filters.tiktok import TikTokVideoLink


async def download_video(message: Message, state: FSMContext):
    status_message = await message.answer('Скачиваю %s' % message.text)
    await message.delete()
    await state.bot.send_chat_action(message.chat.id, 'upload_video')
    try:
        await message.answer_video(
            await TikTokDownloader.get_video_url(message.text),
            caption=f'<b>{message.from_user.username}</b> {message.text}'
        )
    except TelegramBadRequest:
        await status_message.edit_text(
            'Не получилось скачать быстро пробую другой способ %s'
            % message.text
        )
        await message.answer_video(
            await TikTokDownloader.get_video_as_input_file(message.text),
            caption=f'<b>{message.from_user.username}</b> {message.text}'
        )
    except TikTokInvalidUrl:
        await message.answer('Неправильная ссылка %s' % message.text)
    except TikTokDownloadFailed:
        await message.answer('Не получилось скачать %s' % message.text)
    await status_message.delete()


def setup(r: Router):
    r.message.register(
        download_video,
        TikTokVideoLink()
    )
