import asyncio
from collections.abc import AsyncIterator
from unittest.mock import patch

import httpx
import pytest
from openai import AsyncOpenAI

from services.llm.openrouter import OpenRouter


class ModelResponse(httpx.AsyncByteStream):
    def __init__(self) -> None:
        self.closed = False
        self.reading = asyncio.Event()

    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
        self.reading.set()
        await asyncio.Future()

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.parametrize("cancel_while_reading", [False, True])
async def test_closing_model_generator_releases_http_stream_and_client(
    cancel_while_reading: bool,
) -> None:
    body = ModelResponse()
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, headers={"content-type": "text/event-stream"}, stream=body
        )
    )
    http_client = httpx.AsyncClient(transport=transport)
    client = AsyncOpenAI(api_key="test", http_client=http_client)
    with patch("services.llm.openrouter.AsyncOpenAI", return_value=client):
        stream = OpenRouter().stream("prompt")
        assert (await anext(stream)).text == "hello"
        if cancel_while_reading:
            pending = asyncio.create_task(anext(stream))
            await asyncio.wait_for(body.reading.wait(), 1)
            pending.cancel()
            with pytest.raises(asyncio.CancelledError):
                await pending
        else:
            # Stop while the generator is suspended at yield, not reading HTTP.
            await stream.aclose()
    assert body.closed
    assert http_client.is_closed
