"""Compare baseline and production fix on a local snapshot, without network access."""

import argparse
import asyncio
import fcntl
import gc
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from collections.abc import Awaitable, Callable
from functools import partial
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import uvloop

# Run with PYTHONPATH=bot to use the same module names as production and workers.
from services.gkfeed._decoder import FeedDecoder  # pyright: ignore[reportMissingImports]
from services.gkfeed._types import FeedItem, GkfeedCredentials  # pyright: ignore[reportMissingImports]
from services.gkfeed.api import GkfeedApi  # pyright: ignore[reportMissingImports]

BASELINE = "28a0081f7b25ea2c33192b5596d1e22356f1fdd9"
PERIOD = 0.001


def baseline_api_type() -> type[GkfeedApi]:
    source = subprocess.check_output(
        ["git", "show", f"{BASELINE}:bot/services/gkfeed/api.py"], text=True
    )
    module = ModuleType("services.gkfeed._benchmark_baseline")
    # Load only the trusted, pinned repository revision, never the input payload.
    exec(compile(source, "baseline_api.py", "exec"), module.__dict__)  # noqa: S102
    return cast(type[GkfeedApi], module.__dict__["GkfeedApi"])


def snapshot_api(api_type: type[GkfeedApi], payload: bytes) -> GkfeedApi:
    api = api_type(GkfeedCredentials("benchmark", "not-a-credential"))
    # Isolate each benchmark instance, including baseline's class-level state.
    api.__dict__.update(_items_cache={}, _items_lock=asyncio.Lock())

    async def read(url: str) -> bytes:
        return payload

    api.__dict__["_get_html"] = read
    return api


async def consume(api: GkfeedApi) -> list[FeedItem]:
    return [item async for item in api.get_user_items()]


async def measure(operation: Callable[[], Awaitable[Any]]) -> dict[str, Any]:
    ready = asyncio.Event()
    stop = False
    samples: list[tuple[float, float]] = []

    async def heartbeat() -> None:
        while not stop:
            target = time.perf_counter() + PERIOD
            ready.set()
            await asyncio.sleep(PERIOD)
            sampled_at = time.perf_counter()
            samples.append((sampled_at, max(0.0, sampled_at - target) * 1000))

    task = asyncio.create_task(heartbeat())
    await ready.wait()
    await asyncio.sleep(0.003)
    started = time.perf_counter()
    value = await operation()
    ended = time.perf_counter()
    await asyncio.sleep(0.003)
    stop = True
    await task
    assert any(sample < started for sample, _ in samples)
    assert any(sample >= ended for sample, _ in samples)
    return {
        "wall_ms": (ended - started) * 1000,
        "max_lag_ms": max(lag for _, lag in samples),
        "samples_before": sum(sample < started for sample, _ in samples),
        "samples_after": sum(sample >= ended for sample, _ in samples),
        "heartbeat_samples": len(samples),
        "output_count": len(value) if isinstance(value, list) else None,
    }


def summarize(runs: list[dict[str, Any]]) -> dict[str, int | float]:
    result: dict[str, int | float] = {"runs": len(runs)}
    for metric in ("wall_ms", "max_lag_ms"):
        values = sorted(run[metric] for run in runs)
        result[metric + "_median"] = statistics.median(values)
        result[metric + "_p95"] = values[math.ceil(0.95 * len(values)) - 1]
        result[metric + "_worst"] = max(values)
    return result


async def synthetic_probe() -> None:
    time.sleep(0.020)  # noqa: ASYNC251 - deliberate heartbeat validation


async def run(payload: bytes, repeats: int) -> dict[str, Any]:
    baseline_type = baseline_api_type()
    current_cold = snapshot_api(baseline_type, payload)
    current_hot = snapshot_api(baseline_type, payload)
    fixed_cold = snapshot_api(GkfeedApi, payload)
    fixed_hot = snapshot_api(GkfeedApi, payload)
    decoder = FeedDecoder()
    fixed_cold.__dict__["_items_decoder"] = decoder
    fixed_hot.__dict__["_items_decoder"] = decoder
    results: dict[str, list[dict[str, Any]]] = {}
    try:
        results["idle_before"] = [
            await measure(lambda: asyncio.sleep(0.010)) for _ in range(repeats)
        ]
        results["synthetic_sync_sleep_20ms"] = [
            await measure(synthetic_probe) for _ in range(5)
        ]
        assert (
            min(sample["max_lag_ms"] for sample in results["synthetic_sync_sleep_20ms"])
            >= 18
        )
        results["fixed_lazy_first_miss"] = []
        for _ in range(5):
            lazy_decoder = FeedDecoder()
            lazy_api = snapshot_api(GkfeedApi, payload)
            lazy_api.__dict__["_items_decoder"] = lazy_decoder
            try:
                results["fixed_lazy_first_miss"].append(
                    await measure(partial(consume, lazy_api))
                )
            finally:
                await lazy_decoder.close()
            lazy_api._items_cache.clear()
            gc.collect()
        await decoder.start()
        expected = await consume(current_hot)
        actual = await consume(fixed_hot)
        assert actual == expected  # Compare every field, including all text/base64.
        output_count = len(expected)
        del actual, expected
        cases: dict[str, tuple[GkfeedApi, bool]] = {
            "current_cold": (current_cold, True),
            "current_hot": (current_hot, False),
            "fixed_cold_warm_worker": (fixed_cold, True),
            "fixed_hot": (fixed_hot, False),
        }
        for api, cold in cases.values():
            await consume(api)
            if cold:
                api._items_cache.clear()
        results.update({name: [] for name in cases})
        randomizer = random.Random(20261022)
        for _ in range(repeats):
            order = list(cases)
            randomizer.shuffle(order)
            for name in order:
                api, cold = cases[name]
                if cold:
                    api._items_cache.clear()
                gc.collect()
                sample = await measure(partial(consume, api))
                assert sample["output_count"] == output_count
                results[name].append(sample)
        results["idle_after"] = [
            await measure(lambda: asyncio.sleep(0.010)) for _ in range(repeats)
        ]
    finally:
        await decoder.close()
    return {
        name: {"runs": runs, "summary": summarize(runs)}
        for name, runs in results.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repeats", default=20, type=int)
    parser.add_argument(
        "--lock",
        default=Path("/tmp/gkbot-feed-loop-audit-20261021/measurement.lock"),
        type=Path,
    )
    args = parser.parse_args()
    payload = args.input.read_bytes()
    result: dict[str, Any] = {
        "baseline": BASELINE,
        "input_bytes": len(payload),
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "python": sys.version,
        "gil_enabled": sys._is_gil_enabled(),
        "uvloop": importlib.metadata.version("uvloop"),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "heartbeat_period_ms": 1,
        "percentile": "nearest rank over per-run maximum heartbeat lag",
        "isolation": "resident bytes, no network; input read, GC and cleanup outside timing",
        "process": "one spawned worker; input/output IPC included; startup excluded except lazy case",
    }
    args.lock.parent.mkdir(parents=True, exist_ok=True)
    print("Waiting for shared measurement lock", flush=True)
    with args.lock.open("a") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        result["started_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        result["results"] = uvloop.run(run(payload, args.repeats))
        result["finished_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {name: case["summary"] for name, case in result["results"].items()},
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
