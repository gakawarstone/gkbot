from typing import Any

from services.repositories.books import BooksRepository

from ...states import FSM
from ._base import BaseHandler


class ChangeBookPropertyHandler(BaseHandler):
    async def handle(self) -> Any:
        if self.ctx.book_id is None:
            raise ValueError("book_id is required")
        if self.ctx.property_name is None:
            raise ValueError("property_name is required")

        if self.event.from_user is None:
            await self.event.answer("Не удалось определить пользователя")
            return

        try:
            await BooksRepository.edit_book_property(
                book_id=self.ctx.book_id,
                user_id=self.event.from_user.id,
                property_name=self.ctx.property_name,
                new_property_value=self.ctx.new_value,
            )
        except ValueError as exc:
            await self.event.answer(str(exc))
            return
        await self.state.set_state(FSM.check_menu_command)
        await self.event.answer("Успешно изменено")
