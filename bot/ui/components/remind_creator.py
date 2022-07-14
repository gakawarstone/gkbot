from .base import BaseComponent


class RemindCreator(BaseComponent):
    def __init__(self, user_id: int) -> None:
        super().__init__(user_id)
        self.__state = 'remind_text'
        self.state = 'remind_text'
        self.text = None
        self.date = None
        self.__time = None
        self.__status_message = None

    async def init(self):
        await self._render()

    async def set_remind_text(self, text: str) -> None:
        # [ ] only after init
        self.__text = text
        self.__state = 'remind_date'
        await self._render()

    async def set_remind_date(self, date: str) -> None:
        # [ ] only after text
        self.__date = date
        self.__state = 'remind_time'
        await self._render()

    async def set_remind_time(self, time: str) -> None:
        # [ ] only after date
        self.__time = time
        self.__state = 'finished'
        await self._render()
        self.clear_status_message()

    async def set_status_finished(self) -> None:
        await self.set_status_message('<u>Создано успешно</u> ✅')
        self.__message = None  # FIXME

    async def set_status_message(self, text: str) -> None:
        self.__status_message = text
        await self._render()
        self.clear_status_message()

    def clear_status_message(self) -> None:
        self.__status_message = None

    @property
    async def content(self):
        text = '<u>Создатель напоминаний ⌚️</u>\n'

        if self.__state == 'remind_text':
            text += '<b>> Текст: ... </b>\n'
        else:
            text += 'Текст: ' + self.__text + '\n'

        if self.__state == 'remind_date':
            text += '<b>> Время: ...</b>\n'
        elif self.__state == 'remind_time':
            text += '<b>>Время: ' + str(self.__date) + ' ...</b>\n'
        elif self.__time:
            text += 'Время: ' + str(self.__date) + ' ' + \
                str(self.__time) + '\n'
        else:
            text += 'Время: \n'

        if self.__status_message:
            text += self.__status_message

        return text
