import logging

from ..bot_config import bot  # [ ] no top level package

logger = logging.getLogger(__name__)


class Channel:
    def __init__(self, chat_id: str) -> None:
        self.chat_id = chat_id

    def post(self, text: str) -> None:
        bot.send_message(text)

    def handler(self):
        pass
