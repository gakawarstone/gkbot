from re import findall
from ast import literal_eval

from services.http import HttpService
from ...types import InfoVideoTikTok
from ...exceptions import TikTokInvalidUrl
from .._base import BaseExtractor
from ..exceptions import SourceInfoExtractFailed
from ._decoder import decoder


class Snaptik(BaseExtractor):
    async def get_video_info(self, url: str) -> InfoVideoTikTok:
        try:
            response = InfoVideoTikTok(
                video_url=await self.get_video_file_url(url),
                music_url="",
                images_urls=[],
            )
            return response
        except IndexError:
            raise SourceInfoExtractFailed(self)

    async def get_video_file_url(self, url: str) -> str:
        return (await self._get_video_links(url))[0]

    async def _get_video_links(self, url: str) -> list[str]:
        resp = await HttpService.post(
            "https://snaptik.app/abc2.php",
            body={
                "url": url,
                "lang": "en",
                **dict(
                    findall(
                        'name="(token)" value="(.*?)"',
                        (await HttpService.get("https://snaptik.app/en")).decode(
                            "utf-8"
                        ),
                    )
                ),
            },
        )
        resp_text = resp.decode("utf-8")

        if "error_api_web;" in resp_text or "Error:" in resp_text:
            raise TikTokInvalidUrl(url)

        dec = decoder(
            *literal_eval(findall(r"\(\".*?,.*?,.*?,.*?,.*?.*?\)", resp_text)[0])
        )

        return [
            link
            for link in set(
                [
                    "https://snaptik.app" + x.strip("\\")
                    for x in findall(r"(/file.php?.*?)\"", dec)
                ]
                + [i.strip("\\") for i in findall(r"\"(https?://snapxcdn.*?)\"", dec)]
            )
        ]
