from typing import Any

from aiogram.types import ReplyKeyboardRemove

from services.pomodoro import Pomodoro as PomodoroService
from contrib.handlers.message.base import BaseHandler
from ui.widgets.timer import Timer
from .restart import ask_to_restart


class PomodoroHandler(BaseHandler):
    __time_focused = 15 * 60
    __time_relax = 15 * 60

    async def handle(self) -> Any:
        await self.event.answer(
            'Вы включили 🕔 <b>помидор</b>',
            reply_markup=ReplyKeyboardRemove()
        )
        await self.__run_timer(
            seconds=self.__time_focused,
            greet_text='У вас <i>15</i> минут <b>будьте сконцентрированы</b>',
            timer_text='<i>Вжаривай по полной</i>'
        )
        await self.__run_timer(
            seconds=self.__time_relax,
            greet_text='Теперь у вас есть время на отдых <i>15 минут</i>',
            timer_text='<i>На чиле</i>'
        )
        cnt = await PomodoroService.increment_today_stat(
            user_id=self.event.from_user.id
        )
        await self.event.answer(
            '<b>Поздравляю</b> вы получили <b>[<i>%s</i>🍅]</b>' % cnt
        )
        await ask_to_restart(self, 'Хотите начать новый помидор?')

    async def __run_timer(self, seconds: int, greet_text, timer_text: str):
        msg = await self.event.answer(greet_text)
        await Timer(self.event, seconds, timer_text).run()
        await msg.delete()
