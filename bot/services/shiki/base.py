import aiohttp
from bs4 import BeautifulSoup


class Shiki:
    url = 'https://shikimori.one'

    @classmethod
    async def get_webpage(cls, user_name: str, path: str) -> BeautifulSoup:
        async with aiohttp.ClientSession(
            headers={'User-Agent': 'Mozilla/5.0'}
        ) as session:
            async with session.get(
                url=f'{cls.url}/{user_name}/{path}',
            ) as response:
                data = await response.json()
        return BeautifulSoup(
            markup=''.join(line for line in data['content']),
            features='html.parser'
        )
