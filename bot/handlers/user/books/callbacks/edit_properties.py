from typing import Any

from ..messages.edit_property._context import EditBookPropertyContextManager
from ..messages.edit_property.start import InitEditBookPropertyHandler
from .base import BaseHandler


class EditHandler(EditBookPropertyContextManager, BaseHandler):
    async def handle(self) -> Any:
        callback_data = await self._parse_callback()
        if callback_data is None:
            return None

        event, book = callback_data

        self.set(self.props.book_id, book.id)
        self.set(self.props.property_name, event)

        await InitEditBookPropertyHandler(
            self.event.message, state=self.state, data=self.data["data"]
        ).handle()
