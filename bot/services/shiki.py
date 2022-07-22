import asyncio
import json
from urllib.request import Request, urlopen

from aiogram import Dispatcher
from bs4 import BeautifulSoup

from lib.meta import MetaSingleton


class Shiki:
    url = 'https://shikimori.one'

    @classmethod
    def get_webpage(cls, user_name: str, path: str) -> BeautifulSoup:
        req = Request(f'{cls.url}/{user_name}/{path}',  # [ ] async
                      headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        data = json.loads(webpage)
        text = ''.join(line for line in data['content'])
        return BeautifulSoup(text, 'html.parser')


class User:
    def __init__(self, name: str) -> None:
        self.name = name
        self.url = Shiki.url + f'/{name}'
        self.updates = UserUpdates(self)

    def __str__(self) -> str:
        return f'Пользователь <a href="{self.url}">@{self.name}</a>\n'


class Update:  # [ ] type hints
    def __init__(self, name_en, name_ru, time, type) -> None:
        self.name_en = name_en
        self.name_ru = name_ru
        self.time = time
        self.type = type

    def __str__(self) -> str:
        return f'<b>{self.name_ru}</b>\n[<i>{self.type}</i>]\n'


class UserUpdates:
    def __init__(self, user: User) -> None:
        self.user = user

    def load_latest(self, max_updates: int) -> list[Update]:
        updates = self.__load(1)  # BUG
        try:
            return updates[:max_updates]
        except(Exception):
            return updates

    def __load(self, page_num: int) -> list[Update]:
        soup = Shiki.get_webpage(self.user.name, f'history/{page_num}.json')
        raw_updates = soup.find_all('p')
        updates = []
        for item in raw_updates:
            try:
                update = Update(
                    name_en=item.span.a.contents[0].text,
                    name_ru=item.span.a.contents[1].text,
                    time=item.time['datetime'],
                    type=''.join(str(i)
                                 for i in item.span.contents[1:])[1:]
                )
                updates.append(update)
            except(Exception):
                continue
        return updates


class UserUpdatesSubscription:
    def __init__(self, chat_id: int, shiki_name: str) -> None:
        self.chat_id = chat_id
        self.user = User(shiki_name)
        self.user_updates = UserUpdates(self.user)
        self.last_update = self.__get_last_update()

    def __get_last_update(self) -> Update:
        return self.user_updates.load_latest(1)[0]

    def is_updated(self) -> bool:
        new_update = self.__get_last_update()
        if (self.last_update.type != new_update.type):
            print(self.last_update.type)  # [ ] logging?
            print(new_update.type)
            self.last_update = new_update
            return True
        else:
            return False


class UserUpdatesDispatcher(metaclass=MetaSingleton):  # BUG
    def __init__(self) -> None:
        self.subscriptions: list[UserUpdatesSubscription] = []

    def add_subscription(self, chat_id, shiki_name) -> None:
        self.subscriptions.append(UserUpdatesSubscription(chat_id, shiki_name))

    async def __dispatcher(self, dp: Dispatcher, delay=60) -> None:
        while True:
            for sub in self.subscriptions:
                if sub.is_updated():
                    update = sub.last_update  # BUG db don't have bot
                    await dp.bot.send_message(sub.chat_id, str(update) + str(sub.user))
            await asyncio.sleep(delay)

    async def on_startup(self, dp: Dispatcher):
        asyncio.create_task(self.__dispatcher(dp))
