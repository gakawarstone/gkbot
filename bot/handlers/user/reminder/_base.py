from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.formatting import Bold, Text, Underline

from ui.components.remind_creator import RemindCreator

from ._context import ReminderContextManager


class _Status:
    invalid_date = Text("❌", Bold("Формат [30.12.2021]"), "❌")
    invalid_time = Text("❌", Bold("Формат [10:14]"), "❌")
    success = Text(Underline("Создано успешно"), " ✅")


class BaseHandler(ReminderContextManager):
    status = _Status

    async def render_widget(self, status_message: Text | None = None) -> None:
        context = self.ctx
        if context.message is None:
            raise ValueError("ctx.message is None")

        text = RemindCreator(
            text=context.text,
            date=context.date,
            time=context.time,
            status_message=status_message,
            tz=context.tz,
        ).as_text()

        try:
            await context.message.edit_text(**text.as_kwargs())
        except TelegramBadRequest:
            pass
