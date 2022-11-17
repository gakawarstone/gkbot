from typing import Any

from services.books import BookService
from ._base import BaseHandler
from ...states import FSM


class ChangeBookPropertyHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.check_menu_command)
        try:
            await BookService.edit_book_property(
                book_id=self.ctx.book_id,
                property_name=self.ctx.property_name,
                new_property_value=self.ctx.new_value
            )
            await self.event.answer('Успешно изменено')
        except:  # FIXME bare exception
            await self.event.answer('Что то пошло не так')
