from typing import Any

from ._base import BaseHandler
from .change_property import ChangeBookPropertyHandler


class GetNewPropertyValueHandler(BaseHandler):
    async def handle(self) -> Any:
        self.set(self.props.new_value, self.event.text)
        await ChangeBookPropertyHandler(
            self.event, state=self.state, data=self.user_data
        ).handle()
