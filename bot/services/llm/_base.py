from abc import ABC, abstractmethod
from typing import NamedTuple, Literal
from collections.abc import AsyncGenerator


class StreamChunk(NamedTuple):
    text: str
    type: Literal["content", "reason"]


class LLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass

    # @abstractmethod # BUG: commented because of fn linter
    async def stream(
        self, prompt: str, images: list[str] | None = None
    ) -> AsyncGenerator[StreamChunk]:
        yield StreamChunk("say tx for linter", "content")
