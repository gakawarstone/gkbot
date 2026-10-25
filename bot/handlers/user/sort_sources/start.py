from typing import Any

from extensions.handlers.message.base import BaseHandler
from extensions.handlers.message.one_time_extension import (
    OneTimeMessageHandlerExtension,
)
from ui.static import Images

from ._states import FSM


class InitHandler(OneTimeMessageHandlerExtension, BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()
        await self.state.set_state(FSM.sort_file)
        text = (
            "Вы включили сортировщик — удобный инструмент, призванный избавить вас от "
            "необходимости вручную обрабатывать данные. 📊\n\n"
            "Он автоматически выполнит всю необходимую работу, сэкономив ваше время и усилия ⏱️💪. \n\n"
            "Просто <b><u>отправьте .txt файл с вашими источниками</u></b> 📂, и система обработает его за вас 🤖."
        )

        self._set_one_time_message(
            await self.event.answer_photo(
                await Images.sort_documents.as_input_file(), caption=text
            )
        )
