from typing import Any

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest

from services.tiktok import TikTokService
from services.tiktok.exceptions import \
    TikTokInvalidUrl, TikTokInfoExtractionFailed, TikTokVideoUrlExtractionFailed
from contrib.handlers.message.base import BaseHandler
from filters.tiktok import TikTokVideoLink


class TikTokVideoHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()
        status_message = await self.event.answer(
            'Скачиваю ' + self._tiktok_link)
        await self.state.bot.send_chat_action(
            self.event.chat.id, 'upload_video')
        try:
            await self._send_tiktok_video(self._tiktok_link)
            await status_message.delete()
        except TikTokInvalidUrl:
            status_text = 'Неправильная ссылка ' + self._tiktok_link
            await status_message.edit_text(status_text)
        except TikTokInfoExtractionFailed:
            status_text = 'Не получилось скачать ' + self._tiktok_link
        else:
            return
        await status_message.edit_text(status_text)

    async def _send_tiktok_video(self, link: str) -> None:
        caption = f'<b>{self.event.from_user.username}</b> {link}'
        try:
            video_url = await TikTokService.get_video_url(link)
            await self.event.answer_video(video_url, caption=caption)
        except (TelegramBadRequest, TikTokVideoUrlExtractionFailed):
            video_file = await TikTokService.get_video_as_input_file(link)
            await self.event.answer_video(video_file, caption=caption)

    @property
    def _tiktok_link(self) -> str:
        return self.event.text


def setup(r: Router):
    r.message.register(TikTokVideoHandler, TikTokVideoLink())
