import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("value, expected", [(None, 10), ("1", 1), ("7", 7)])
def test_polling_config_from_environment(value: str | None, expected: int) -> None:
    result = load_config(value)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(expected)


@pytest.mark.parametrize("value", ["0", "-1", "", "1.5", "unlimited"])
def test_polling_config_rejects_invalid_environment(value: str) -> None:
    result = load_config(value)
    assert result.returncode != 0
    assert "POLLING_TASKS_CONCURRENCY_LIMIT must be a positive integer" in result.stderr


def load_config(value: str | None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    # Isolate import-time config and never read credentials from a local .env.
    environment.update(
        PYTHONPATH="bot",
        PYTHON_DOTENV_DISABLED="1",
        BOT_TOKEN="12345678:ABCDEF-GHIJKLMNOPQRSTUV",
        ADMIN_IDS="1234",
        DB_URL="sqlite://:memory:",
    )
    if value is None:
        environment.pop("POLLING_TASKS_CONCURRENCY_LIMIT", None)
    else:
        environment["POLLING_TASKS_CONCURRENCY_LIMIT"] = value
    return subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from configs.bot_config import BOT_CONFIG; "
                "print(BOT_CONFIG.polling_tasks_concurrency_limit)"
            ),
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
