from typing import Any

from ..messages import edit_property
from .base import BaseHandler


class EditHandler(BaseHandler):
    async def handle(self) -> Any:
        event, book = await self._parse_callback()

        self.ctx['book_id'] = book.id
        self.ctx['book_property_name'] = event

        await edit_property.init(self.event.message,
                                 self.state, self.data['data'])
