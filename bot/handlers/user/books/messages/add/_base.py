from typing import Optional

from aiogram.exceptions import TelegramBadRequest

from ui.components.book_creator import BookCreatorComponent
from ._context import AddBookContextManager


class _Status:
    error = "❌<b>Произошла ошибка</b>❌"
    success = "<u>Создано успешно</u> ✅"


class BaseHandler(AddBookContextManager):
    status = _Status

    async def render_widget(self, status_message: Optional[str] = None):
        if self.ctx.message is None:
            raise ValueError("Message context is not set.")

        text = BookCreatorComponent(
            title=self.ctx.name,
            author=self.ctx.author,
            num_of_pages=self.ctx.chapter_cnt,
            status_message=status_message,
        ).render()

        try:
            await self.ctx.message.edit_text(text)
        except TelegramBadRequest:
            pass
