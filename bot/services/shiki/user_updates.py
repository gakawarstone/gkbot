from .base import Shiki


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

    async def load_latest(self, max_updates: int) -> list[Update]:
        updates = await self.__load(1)
        try:
            return updates[:max_updates]
        except(Exception):
            return updates

    async def __load(self, page_num: int) -> list[Update]:
        soup = await Shiki.get_webpage(self.user.name, f'history/{page_num}.json')
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
