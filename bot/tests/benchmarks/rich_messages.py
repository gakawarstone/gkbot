"""Compare rich conversion with the existing HTML renderer, without Telegram.

Run with PYTHONPATH=bot .venv/bin/python -m tests.benchmarks.rich_messages.
"""

import argparse
import json
import platform
from collections.abc import Callable
from dataclasses import dataclass
from statistics import median
from time import perf_counter_ns

import aiogram

from extensions.handlers.message.markdown_render import parse_markdown, render_html
from services.rich_messages import (
    CodePart,
    DetailsPart,
    ListPart,
    MathPart,
    QuotePart,
    ReasoningPart,
    ResponseParts,
    TextPart,
    to_rich_message,
)


@dataclass(frozen=True, slots=True)
class Fixture:
    name: str
    parts: ResponseParts
    markdown: str


def fixtures() -> list[Fixture]:
    paragraph = "Привет <&> 😀"
    result = [Fixture("plain", (TextPart(paragraph),), paragraph)]
    result.append(
        Fixture(
            "mixed",
            (
                ReasoningPart("Check the formula"),
                TextPart(paragraph),
                CodePart("print('<&>')\n", "python"),
                ListPart(((TextPart("first"),), (TextPart("second"),)), start=1),
                MathPart(r"x^2 + y^2 = z^2"),
                QuotePart((TextPart("quote"),)),
                DetailsPart("More", (TextPart("details"),)),
            ),
            "Check the formula\n\n"
            f"{paragraph}\n\n```python\nprint('<&>')\n```\n\n"
            "1. first\n2. second\n\n$$x^2 + y^2 = z^2$$\n\n"
            "> quote\n\nMore\n\ndetails",
        )
    )
    for depth in (4, 8, 16):
        parts: ResponseParts = (TextPart(paragraph),)
        for _ in range(depth - 1):
            parts = (DetailsPart("More", parts),)
        result.append(
            Fixture(f"nested_{depth}", parts, "More\n\n" * (depth - 1) + paragraph)
        )
    large_paragraph = (paragraph + " ") * 100
    result.append(
        Fixture(
            "large",
            tuple(TextPart(large_paragraph) for _ in range(40)),
            "\n\n".join([large_paragraph] * 40),
        )
    )
    return result


def measure(operation: Callable[[], bytes], iterations: int) -> dict[str, float | int]:
    payload = operation()  # Warm imports and validators before measuring.
    times = []
    for _ in range(iterations):
        start = perf_counter_ns()
        operation()
        times.append((perf_counter_ns() - start) / 1_000_000)
    return {
        "median_ms": round(median(times), 4),
        "max_ms": round(max(times), 4),
        "payload_bytes": len(payload),
    }


def benchmark(iterations: int) -> dict[str, object]:
    return {
        "python": platform.python_version(),
        "aiogram": aiogram.__version__,
        "iterations": iterations,
        "results": [measure_fixture(fixture, iterations) for fixture in fixtures()],
    }


def measure_fixture(fixture: Fixture, iterations: int) -> dict[str, object]:
    return {
        "fixture": fixture.name,
        "rich": measure(
            lambda: json.dumps(
                to_rich_message(fixture.parts).model_dump(
                    mode="json", exclude_none=True
                )
            ).encode("utf-8"),
            iterations,
        ),
        "html": measure(
            lambda: render_html(parse_markdown(fixture.markdown)).encode("utf-8"),
            iterations,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error("iterations must be positive")
    print(json.dumps(benchmark(args.iterations), indent=2))


if __name__ == "__main__":
    main()
