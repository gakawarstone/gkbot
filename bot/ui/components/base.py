from abc import ABC, abstractmethod
from settings import mng


class BaseComponent(ABC):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.__message = None
        self._state = None
        self.__rendered_text = None

    @property
    @abstractmethod
    async def content(self):
        pass

    async def _render(self):
        if not self.__message:
            self.__message = await mng.send_message(
                self.user_id, await self.content)
        elif await self.content != self.__rendered_text:
            await self.__message.edit_text(await self.content)

        self.__rendered_text = self.content
