from typing import Any

from models.books import Book  # FIXME should service
from ._base import BaseHandler
from ...states import FSM


class CreateBookHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.check_menu_command)
        _, is_created = await Book.get_or_create(
            name=self.ctx.name,
            author=self.ctx.author,
            chapters_cnt=self.ctx.chapter_cnt,
            user_id=self.event.from_user.id,
        )
        if not is_created:
            await self.render_widget(self.status.error)
        else:
            await self.render_widget(self.status.success)
