from collections.abc import AsyncGenerator
from enum import Enum

from openai import AsyncOpenAI

from configs.env import OPENROUTER_API_KEY

from ._base import LLM, StreamChunk


class OpenRouterModel(Enum):
    GEMMA_4 = "google/gemma-4-31b-it:free"
    GPT_5_6_LUNA = "openai/gpt-5.6-luna"

    @property
    def supports_images(self) -> bool:
        return self in {
            OpenRouterModel.GEMMA_4,
            OpenRouterModel.GPT_5_6_LUNA,
        }


DEFAULT_MODEL = OpenRouterModel.GPT_5_6_LUNA


class OpenRouter(LLM):
    def __init__(self, model: OpenRouterModel = DEFAULT_MODEL) -> None:
        self._model = model.value

    async def generate(self, prompt: str) -> str:
        result = ""
        async for chunk in self.stream(prompt):
            result += chunk.text
        return result

    async def stream(
        self, prompt: str, images: list[str] | None = None
    ) -> AsyncGenerator[StreamChunk]:
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        content: list[dict[str, str | dict[str, str]]] = [
            {"type": "text", "text": prompt}
        ]

        if images:
            for image_url in images:
                content.append({"type": "image_url", "image_url": {"url": image_url}})

        completion = await client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": content}],  # type: ignore
            stream=True,
        )

        async for chunk in completion:  # type: ignore
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, "reasoning", None)
            if reasoning:
                yield StreamChunk(reasoning, "reason")
            content_piece = getattr(delta, "content", None)
            if content_piece:
                yield StreamChunk(content_piece, "content")
