from typing import Any, Sequence
import asyncio
import json

from configs.env import BROKER_URL
from services.http import HttpService


async def get_info(url: str) -> dict:
    resp = await _put_and_wait_for_result("ytdlp.extract_info", [url])
    return json.loads(resp)


async def download_video(url: str, opts: dict) -> str:
    return await _put_and_wait_for_result("ytdlp.download_video", [url, opts])


async def _put_and_wait_for_result(func: str, args: Sequence[Any]) -> Any:
    task_id = await _enqueue(func, args)
    status = await _get_status(task_id)
    while status != "completed":
        status = await _get_status(task_id)
        await asyncio.sleep(1)
    return await _get_result(task_id)


async def _get_result(task_id: str) -> Any:
    response = await HttpService.get_json(BROKER_URL + "/result/" + task_id)
    return response["result"]


async def _get_status(task_id: str) -> str:
    response = await HttpService.get_json(BROKER_URL + "/result/" + task_id)
    return response["status"]


async def _enqueue(func: str, args: Sequence[Any]) -> str:
    response = await HttpService.post_json(
        BROKER_URL + "/enqueue", {"function": func, "data": args}
    )
    return response["task_id"]
