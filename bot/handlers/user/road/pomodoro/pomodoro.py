from typing import Any

from aiogram.types import ReplyKeyboardRemove

from services.pomodoro import Pomodoro as PomodoroService
from ._base import BaseHandler
from .restart import ask_to_restart


class PomodoroHandler(BaseHandler):
    async def handle(self) -> Any:
        if self.event.from_user is None:
            raise ValueError("from_user is None")

        await self.event.answer(
            "Вы включили 🕔 <b>помидор</b>", reply_markup=ReplyKeyboardRemove()
        )

        await self.run_timer(
            time=(await self.settings).time_focused,
            greet_text="У вас <i>15</i> минут <b>будьте сконцентрированы</b>",
            timer_text="<i>Вжаривай по полной</i>",
        )

        await self.run_timer(
            time=(await self.settings).time_relax,
            greet_text="Теперь у вас есть время на отдых <i>15 минут</i>",
            timer_text="<i>На чиле</i>",
        )

        cnt = await PomodoroService.increment_today_stat(
            user_id=self.event.from_user.id
        )
        await self.event.answer(
            "<b>Поздравляю</b> вы получили <b>[<i>%s</i>🍅]</b>" % cnt
        )

        await ask_to_restart(self, "Хотите начать новый помидор?")
