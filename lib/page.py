from notion_client import AsyncClient
from typing import Optional

from bot_config import NOTION_API_TOKEN
client = AsyncClient(auth=NOTION_API_TOKEN)


class TextBlock:
    def __init__(self, text: str):
        self.text = text
        self.data = self.__get_data()

    def __get_data(self):
        return {'object': 'block',
                'type': 'paragraph',
                'paragraph': {
                    'text': [{
                        'type': 'text',
                        'text': {
                            'content': self.text
                        }
                    }]
                }}


class Page:
    def __init__(self, id):
        self.id = id

    async def write(self, text: str):
        await self.add_children([TextBlock(text).data])

    async def add_children(self, children: list[str]) -> str:
        return await client.blocks.children.append(self.id, children=children)


class Database(Page):
    async def add_row(self, title: str) -> Page:
        properties = {
            'Name': {'title': [{'text': {'content': title}}]}
        }
        return await self.__create_page(properties)

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
