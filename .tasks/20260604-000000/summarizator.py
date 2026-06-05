from typing import AsyncGenerator

from services.llm import OpenRouter
from services.llm.openrouter import OpenRouterModel


class Summarizator:
    _MODEL = OpenRouterModel.GPT_OSS_120

    @classmethod
    async def stream(cls, text: str) -> AsyncGenerator[str, None]:
        async for ch in OpenRouter(cls._MODEL).stream(
            f"""
            Сделай выжимку из этого текста размером с один абзац

            {text}
            """,
        ):
            yield ch.text
