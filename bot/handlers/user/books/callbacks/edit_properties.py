from typing import Any

from ..messages.edit_property.start import InitEditBookPropertyHandler
from .base import BaseHandler


class EditHandler(BaseHandler):
    async def handle(self) -> Any:
        event, book = await self._parse_callback()

        self.ctx['book_id'] = book.id
        self.ctx['book_property_name'] = event

        await InitEditBookPropertyHandler(
            self.event.message, state=self.state, data=self.data['data']
        ).handle()
