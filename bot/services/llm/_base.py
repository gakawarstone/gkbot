from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, NamedTuple, Literal


class StreamChunk(NamedTuple):
    text: str
    type: Literal["content", "reason"]


class LLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass

    # @abstractmethod # BUG: commented because of fn linter
    async def stream(
        self, prompt: str, images: Optional[list[str]] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        yield StreamChunk("say tx for linter", "content")
