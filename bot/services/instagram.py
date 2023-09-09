from bs4 import BeautifulSoup
from aiogram.types import InputMediaPhoto, FSInputFile

from services.http import HttpService
from services.cache_dir import CacheDir


class InstagramService:
    _download_endpoint = 'https://dumpoir.com/download'
    _headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            'AppleWebKit/537.36 (KHTML, like Gecko)'
            'Chrome/106.0.0.0 Safari/537.36'
        ),
        'Referer': 'https://dumpoir.com/download',
    }

    @ classmethod
    async def get_photos_album(cls, url: str) -> list[InputMediaPhoto]:
        links = await cls._extract_links(url)
        return [
            InputMediaPhoto(media=file)
            for file in await cls._download_photos(links)
        ]

    @ classmethod
    async def _extract_links(cls, url: str) -> list[str]:
        cookie = await HttpService.extract_cookies(
            cls._download_endpoint,
            headers=cls._headers
        )
        cls._headers['Cookie'] = str(cookie).split(': ')[1].split(';')[0]

        data = await cls._prepare_payload(url)
        resp = await HttpService.post(
            cls._download_endpoint,
            body=data,
            headers=cls._headers
        )

        soup = BeautifulSoup(resp, 'html.parser')
        return [i['src'] for i in soup.find_all('img')[1:-1]]

    @ classmethod
    async def _prepare_payload(cls, url: str) -> str:
        html = await HttpService.get(
            cls._download_endpoint,
            headers=cls._headers
        )
        soup = BeautifulSoup(html, 'html.parser')
        csrf = soup.find_all('input')[1]['value']

        return {
            '_csrf_token': csrf,
            'download_form[url]': url,
        }

    @ classmethod
    async def _download_photos(cls, links: list[str]) -> list[FSInputFile]:
        cache_dir = CacheDir()

        for n, link in enumerate(links):
            content = await HttpService.get(link, headers=cls._headers)
            cache_dir.save_file(f'{n}.jpg', content)

        return [
            FSInputFile(f'{cache_dir.path}/{n}.jpg')
            for n, _ in enumerate(links)
        ]
