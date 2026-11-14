import json
import re
from typing import ClassVar

from services.http import HttpService

from ._base import VideoUrlExtractor


class Tikdown(VideoUrlExtractor):
    _base_url = "https://tikdown.org/"
    _headers: ClassVar[dict[str, str]] = {
        "origin": "https://tikdown.org",
        "referer": "https://tikdown.org/",
        "sec-ch-ua": '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/94.0.4606.81 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    async def _get_video_links(self, url: str) -> list[str]:
        res_text = (await HttpService.get(self._base_url)).decode("utf-8")
        _token = re.findall(r'type\="hidden".*?value\="([0-9a-zA-Z]+)"', res_text)[0]
        self._headers.update({"x-csrf-token": _token})
        resp = (
            await HttpService.post(
                self._base_url + "getAjax",
                body={"url": url, "_token": _token},
                headers=self._headers,
            )
        ).decode("utf-8")
        js = json.loads(resp)
        if not isinstance(js, dict):
            raise TypeError("Tikdown returned a non-object response")
        if js.get("status"):
            video = re.findall(r"\"(https?://.*?\.mp4)\"", js["html"])[0]
            return [video]
        return []
