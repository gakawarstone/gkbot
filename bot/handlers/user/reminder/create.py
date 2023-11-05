from typing import Any
from datetime import datetime, timezone

from services.reminder import Reminder
from ._base import BaseHandler


class CreateRemindHandler(BaseHandler):
    async def handle(self) -> Any:  # [ ] if unsuccessful
        await Reminder.add_remind(self.event.from_user.id, self.datetime, self.ctx.text)

        await self.render_widget(status_message=self.status.success)

    @property
    def datetime(self) -> datetime:
        tz = timezone(self.ctx.tz)
        return datetime.combine(self.ctx.date, self.ctx.time, tz)
