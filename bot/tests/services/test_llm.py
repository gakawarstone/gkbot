import asyncio

from services.llm import OpenRouter

from .. import integration_test


async def stream_open_router_response():
    o = OpenRouter()
    async for chunk in o.stream(prompt="Что такое деконструкция"):
        assert len(chunk.text) != 0


@integration_test
async def test_event_loop_not_blocked():
    started = asyncio.Event()
    finished = asyncio.Event()

    async def probe():
        started.set()
        await asyncio.sleep(0.01)
        finished.set()

    task1 = asyncio.create_task(stream_open_router_response())
    task2 = asyncio.create_task(stream_open_router_response())
    task3 = asyncio.create_task(probe())

    await started.wait()
    try:
        await asyncio.wait_for(finished.wait(), timeout=0.02)
        loop_blocked = False
    except TimeoutError:
        loop_blocked = True

    await task1
    await task2
    await task3
    assert not loop_blocked, "Function blocked the event loop!"
