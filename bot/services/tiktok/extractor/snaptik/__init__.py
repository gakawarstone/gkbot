from ast import literal_eval
from re import findall

from services.http import HttpService

from ...exceptions import TikTokInvalidUrl
from .._base import BaseExtractor, VideoUrlExtractor
from ._decoder import decoder


class Snaptik(VideoUrlExtractor):
    _expected_errors = (*BaseExtractor._expected_errors, TikTokInvalidUrl, SyntaxError)

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
