import asyncio

from services.llm import Gemini
from tests import integration_test


@integration_test
async def test_stream_response():
    async for chunk in Gemini.stream("Что такое деконструкция"):
        assert type(chunk) == str
        assert len(chunk) != 0


@integration_test
async def test_event_loop_not_blocked():
    loop = asyncio.get_event_loop()
    started = asyncio.Event()
    finished = asyncio.Event()

    async def probe():
        started.set()
        await asyncio.sleep(0.01)
        finished.set()

    # Start both the probe and the function under test
    task1 = asyncio.create_task(test_stream_response())
    task2 = asyncio.create_task(probe())

    await started.wait()
    try:
        await asyncio.wait_for(finished.wait(), timeout=0.02)
        loop_blocked = False
    except asyncio.TimeoutError:
        loop_blocked = True

    await task1  # Ensure the main task completes
    assert not loop_blocked, "Function blocked the event loop!"
