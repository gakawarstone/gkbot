import json
from pprint import pprint
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup


class ShikiUpdate:
    def __init__(self) -> None:
        self.data = {}


req = Request('https://shikimori.one/gakawarstone/history/1.json',
              headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()
data = json.loads(webpage)

text = ''
for line in data['content']:
    text += line

soup = BeautifulSoup(text, 'html.parser')
updates = soup.find_all('p')

shiki_list = []

for update in updates:
    item = ShikiUpdate()
    item.data['name-en'] = update.span.a.contents[0].text
    item.data['name-ru'] = update.span.a.contents[1].text
    item.data['update-time'] = update.time['datetime']
    item.data['update-type'] = ''.join(str(i)
                                       for i in update.span.contents[1:])[1:]
    shiki_list.append(item.data)
    pprint(shiki_list)
    # print(''.join(str(i) for i in update.span.contents[1:]))
