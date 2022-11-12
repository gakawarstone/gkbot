from typing import Optional

from aiogram.exceptions import TelegramBadRequest

from ui.components.remind_creator import RemindCreator
from ._context import ReminderContextManager


class _Status:
    invalid_date = '❌<b>Формат [30.12.2021]</b>❌'
    invalid_time = '❌<b>Формат [10:14]</b>❌'
    success = '<u>Создано успешно</u> ✅'


class BaseHandler(ReminderContextManager):
    status = _Status

    async def render_widget(self, status_message: Optional[str] = None):
        text = RemindCreator(
            text=self.ctx.text,
            date=self.ctx.date,
            time=self.ctx.time,
            status_message=status_message
        ).render()

        try:
            await self.ctx.message.edit_text(text)
        except TelegramBadRequest:
            pass
