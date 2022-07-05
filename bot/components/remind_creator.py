from settings import bot
# [ ] add base component


class RemindCreator:
    __state = 'remind_text'
    __rendered_text = None
    __message = None
    __text = None
    __date = None
    __time = None
    __status_message = None

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    async def init(self):
        self.__state = 'remind_text'
        await self.__render()

    async def set_remind_text(self, text: str) -> None:
        # [ ] only after init
        self.__text = text
        self.__state = 'remind_date'
        await self.__render()

    async def set_remind_date(self, date: str) -> None:
        # [ ] only after text
        self.__date = date
        self.__state = 'remind_time'
        await self.__render()

    async def set_remind_time(self, time: str) -> None:
        # [ ] only after date
        self.__time = time
        self.__state = 'finished'
        await self.__render()
        self.clear_status_message()

    async def set_status_finished(self) -> None:
        await self.set_status_message('<u>Создано успешно</u> ✅')

    async def set_status_message(self, text: str) -> None:
        self.__status_message = text
        await self.__render()
        self.clear_status_message()

    def clear_status_message(self) -> None:
        self.__status_message = None

    async def __render(self):  # [ ] as decorator
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

        if not self.__message:
            self.__message = await bot.send_message(self.user_id, text)
        elif text != self.__rendered_text:
            await self.__message.edit_text(text)

        self.__rendered_text = text
