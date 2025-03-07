from configs.env import GEMINI_API_KEY
from services.http import HttpService


class Gemini:
    @classmethod
    async def generate(cls, prompt: str) -> str:
        base_api_url = "https://generativelanguage.googleapis.com/v1beta"
        url = f"{base_api_url}/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = await HttpService.post_json(url, body)
        return resp["candidates"][0]["content"]["parts"][0]["text"]
