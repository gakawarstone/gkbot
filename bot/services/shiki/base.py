import json
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


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
