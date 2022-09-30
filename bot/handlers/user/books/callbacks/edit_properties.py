from typing import Any

from .. import edit_book
from .base import BaseHandler


class EditHandler(BaseHandler):
    async def handle(self) -> Any:
        event, book = await self._parse_callback()

        # FIXME type date and set it as property
        self.data['data']['book_id'] = book.id
        self.data['data']['book_property_name'] = event

        await edit_book.init(self.event.message, self.state, self.data['data'])
