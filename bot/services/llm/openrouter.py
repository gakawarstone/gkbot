from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from enum import Enum


from configs.env import OPENROUTER_API_KEY
from ._base import LLM, StreamChunk


class OpenRouterModel(Enum):
    MICROSOFT_PHI_4_REASONING = "microsoft/phi-4-reasoning:free"
    DEEPSEEK_DEEPSEEK_R1_0528 = "deepseek/deepseek-r1-0528:free"
    STEP_35 = "stepfun/step-3.5-flash:free"
    GEMMA_4 = "google/gemma-4-31b-it:free"
    KIMI_K25 = "moonshotai/kimi-k2.5"
    GEMINI_3_FLASH = "google/gemini-3-flash-preview"
    GPT_OSS_120 = "openai/gpt-oss-120b:free"

    @property
    def supports_images(self) -> bool:
        return self in {
            OpenRouterModel.GEMMA_4,
            OpenRouterModel.GEMINI_3_FLASH,
        }


class OpenRouter(LLM):
    def __init__(self, model: OpenRouterModel) -> None:
        self._model = model.value

    async def generate(self, prompt: str) -> str:
        result = ""
        async for chunk in self.stream(prompt):
            result += chunk.text
        return result

    async def stream(
        self, prompt: str, images: Optional[list[str]] = None
    ) -> AsyncGenerator[StreamChunk, None]:
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
