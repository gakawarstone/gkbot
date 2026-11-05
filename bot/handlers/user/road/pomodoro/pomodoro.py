from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from services.pomodoro import Pomodoro as PomodoroService
from ui.keyboards.bool import BoolMarkup

from ..states import FSM
from ._base import BaseHandler


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
            f"<b>Поздравляю</b> вы получили <b>[<i>{cnt}</i>🍅]</b>"
        )

        message = await self.event.answer(
            "Хотите начать новый помидор?", reply_markup=BoolMarkup.yes_or_no
        )
        self.user_data["delete_queue"].append(message)
        await self.state.set_state(FSM.choose_bool)
        self.user_data["callback"] = self


async def choose_bool(message: Message, state: FSMContext, data: dict) -> None:
    callback: PomodoroHandler | None = data.pop("callback", None)
    if callback is None:
        return
    await state.set_state(FSM.finish)
    await message.delete()
    if message.text in (BoolMarkup.buttons.yes, "y"):
        await callback.handle()
