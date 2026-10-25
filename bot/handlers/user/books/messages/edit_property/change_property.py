from typing import Any

from aiogram.exceptions import TelegramBadRequest

from services.repositories.books import BooksRepository

from ...states import FSM
from ._base import BaseHandler


class ChangeBookPropertyHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)

        if self.ctx.book_id is None:
            raise ValueError("book_id is required")
        if self.ctx.property_name is None:
            raise ValueError("property_name is required")

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
