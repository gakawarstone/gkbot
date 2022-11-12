from typing import Any
from datetime import datetime


from services.reminder import Reminder
from ._base import BaseHandler


class CreateRemindHandler(BaseHandler):
    async def handle(self) -> Any:  # [ ] if unsuccess
        Reminder.add_remind(self.event.from_user.id,
                            self.datetime, self.ctx.text)

        await self.render_widget(status_message=self.status.success)

    @property
    def datetime(self) -> datetime:
        # [ ] add timezone to combine
        return datetime.combine(self.ctx.date, self.ctx.time)
