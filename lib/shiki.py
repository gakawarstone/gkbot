import json
from pprint import pprint
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup


class Shiki:
    url = 'https://shikimori.one'

    @classmethod
    def get_webpage(cls, user_name: str, path: str) -> BeautifulSoup:
        req = Request(f'{cls.url}/{user_name}/{path}',
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


class Update:
    def __init__(self) -> None:
        self.name_en = ''
        self.name_ru = ''
        self.time = ''
        self.type = ''


class UserUpdates:
    def __init__(self, user: User) -> None:
        self.user = user

    def load_latest(self, max_updates: int) -> list[Update]:
        updates = self.__load(1)
        try:
            return updates[:max_updates]
        except(Exception):
            return updates

    def __load(self, page_num: int) -> list[Update]:
        soup = Shiki.get_webpage(self.user.name, f'history/{page_num}.json')
        raw_updates = soup.find_all('p')
        updates = []
        for item in raw_updates:
            update = Update()
            update.name_en = item.span.a.contents[0].text
            update.name_ru = item.span.a.contents[1].text
            update.time = item.time['datetime']
            update.type = ''.join(str(i)
                                  for i in item.span.contents[1:])[1:]
            updates.append(update)
        return updates


class UserUpdatesDispatcher:
    def __init__(self) -> None:
        pass
