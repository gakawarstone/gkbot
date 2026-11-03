from typing import Any, override

from ui.keyboards.chat import ChatMarkup

from ._base import BaseHandler
from ._context import _ChatGPTKeys
from ._states import FSM


class InitHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()
        self.clean_context()

        assert self.ctx.messages is not None
        self.ctx.messages.append(
            """
            Ты должен отвечать коротко и по существу, не добавляя лишних слов.
            Если тебе задают вопрос, на который ты не знаешь ответа,
            просто скажи, что не знаешь."
            """
        )

        response = self.event.answer(
            "AI-чат включён. Все следующие сообщения будут отправлены модели. "
            "Чтобы выйти, нажми кнопку ниже или отправь /exit.",
            reply_markup=ChatMarkup.menu,
        )
        response.message_thread_id = self.event.message_thread_id
        await response
        await self.state.set_state(FSM.get_message)

    @override
    def clean_context(self, *args: _ChatGPTKeys) -> None:
        super().clean_context(*args)
        self.set(self.keys.messages, [])
