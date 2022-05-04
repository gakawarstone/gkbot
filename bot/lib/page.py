from notion_client import AsyncClient
from typing import Optional
from datetime import datetime

from bot_config import NOTION_API_TOKEN
client = AsyncClient(auth=NOTION_API_TOKEN)


class TextBlock:
    def __init__(self, text: str):
        self.text = text
        self.data = self.__get_data()

    def __get_data(self) -> dict:
        return {'object': 'block',
                'type': 'paragraph',
                'paragraph': {'text': [{'type': 'text',
                                        'text': {'content': self.text}}]}}


class Page:
    def __init__(self, id: str):
        self.id = id

    async def get_url(self) -> str:
        data = await self.get_data()
        return data['url']

    async def set_properties(self, properties: dict):
        await client.pages.update(page_id=self.id, properties=properties)

    async def write(self, text: str):
        await self.add_children([TextBlock(text).data])

    async def add_children(self, children: list[dict]) -> dict:
        return await client.blocks.children.append(self.id, children=children)

    async def get_all_children_titles(self) -> list:
        data = await client.blocks.children.list(self.id)
        children = data['results']
        outp = []
        for child in children:
            if child['paragraph']['text']:
                title = child['paragraph']['text'][0]['plain_text']
                outp.append(title)
        return outp

    async def get_data(self) -> dict:
        return await client.pages.retrieve(self.id)


class Row(Page):
    async def set_name(self, name: str):
        properties = {'Name': {'title': [{'text': {'content': name}}]}}
        await self.set_properties(properties)

    async def set_date(self, property_name: str, date: datetime):
        date = datetime.strftime(date, '%Y-%m-%d')
        await self.set_properties({property_name: {'date': {'start': date}}})

    async def set_select(self, property_name: str, select: str):
        properties = {property_name: {'select': {'name': select}}}
        await self.set_properties(properties)


class Database(Page):
    async def add_row(self, title: str = 'Processing') -> Row:
        properties = {
            'Name': {'title': [{'text': {'content': title}}]}
        }
        page = await self.__create_page(properties)
        return Row(page.id)

    async def __create_page(self, properties: dict) -> Page:
        response = await client.pages.create(parent={'database_id': self.id},
                                             properties=properties)
        return Page(response['id'])

    async def get_data(self, filter: Optional[dict] = None) -> dict:
        if filter:
            return await client.databases.query(database_id=self.id,
                                                filter=filter)
        else:
            return await client.databases.query(database_id=self.id)
