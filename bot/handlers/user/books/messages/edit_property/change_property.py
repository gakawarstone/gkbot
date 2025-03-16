from aiogram.exceptions import TelegramBadRequest

from typing import Any

from services.repositories.books import BooksRepository
from ._base import BaseHandler
from ...states import FSM


class ChangeBookPropertyHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.check_menu_command)
        try:
            await BooksRepository.edit_book_property(
                book_id=self.ctx.book_id,
                property_name=self.ctx.property_name,
                new_property_value=self.ctx.new_value,
            )
            await self.event.answer("Успешно изменено")
        except TelegramBadRequest:
            await self.event.answer("Что то пошло не так")
