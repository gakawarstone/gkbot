from typing import Any
from datetime import datetime, timezone

from services.reminder import Reminder
from ._base import BaseHandler


class CreateRemindHandler(BaseHandler):
    async def handle(self) -> Any:
        if self.event.from_user is None or self.ctx.text is None:
            raise ValueError("User and text must be provided in the context.")

        await Reminder.add_remind(self.event.from_user.id, self.datetime, self.ctx.text)

        await self.render_widget(status_message=self.status.success)

    @property
    def datetime(self) -> datetime:
        if self.ctx.tz is None or self.ctx.date is None or self.ctx.time is None:
            raise ValueError("Timezone, date, and time must be set in the context.")

        tz = timezone(self.ctx.tz)
        return datetime.combine(self.ctx.date, self.ctx.time, tz)
