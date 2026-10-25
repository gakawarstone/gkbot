from typing import Any

from services.repositories.books import BooksRepository

from ...states import FSM
from ._base import BaseHandler


class CreateBookHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.check_menu_command)
        name = self.ctx.name
        author = self.ctx.author
        chapters_cnt = self.ctx.chapter_cnt
        if name is None or author is None or chapters_cnt is None:
            raise ValueError("Book details are incomplete")
        _, is_created = await BooksRepository.get_or_create_book(
            name=name,
            author=author,
            chapters_cnt=chapters_cnt,
            user_id=self.event.from_user.id,
        )
        if not is_created:
            await self.render_widget(self.status.error)
        else:
            await self.render_widget(self.status.success)
